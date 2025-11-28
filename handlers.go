package main

import (
	"fmt"
	"log"
	"math"
	"net/http"
	"strconv"
	"time"

	"google.golang.org/api/sheets/v4"
)

func (app *application) tester(w http.ResponseWriter, r *http.Request) {
	log.Println("tester was hit")
	app.render(w, http.StatusOK, "home.html", nil)
}

func (app *application) home(w http.ResponseWriter, r *http.Request) {
	readRange := "Items!A2:A"
	resp, err := app.sheetsServices.Spreadsheets.Values.Get(app.sheetID, readRange).Do()
	if err != nil {
		log.Printf("failed to read items: %v", err)
	}

	seen := make(map[string]struct{})
	var Items []string
	for _, row := range resp.Values {
		if len(row) > 0 {
			item := fmt.Sprintf("%v", row[0])
			if _, exists := seen[item]; !exists {
				seen[item] = struct{}{}
				Items = append(Items, item)
			}
		}
	}

	data := map[string]any{
		"Items": Items,
	}
	app.render(w, http.StatusOK, "home.html", data)
}

type IngredientAmount struct {
	Name     string
	Quantity int
}

type ItemCost struct {
	Count      int
	TotalSpent float64
}

type IngredientCost struct {
	Quantity   int
	TotalSpend float64
}

func parseQuantity(quantityStr, unit string) int {
	val, _ := strconv.ParseFloat(quantityStr, 64)

	switch unit {
	case "kg":
		return int(val * 1000) // convert to grams
	case "L":
		return int(val * 1000) // convert to ml
	default:
		return int(val) // g, ml, pcs
	}
}

func parsePricePerSmallestUnit(priceStr, unit string) float64 {
	price, _ := strconv.ParseFloat(priceStr, 64)

	switch unit {
	case "kg", "L":
		return price / 1000.0
	default:
		return price
	}
}

func round(price float64) float64 {
	return math.Round(price*100) / 100
}

func convertToOriginalUnit(quantity int, unit string) float64 {
	switch unit {
	case "kg", "L":
		return float64(quantity) / 1000.0
	default:
		return float64(quantity) // g, ml, pcs
	}
}

func (app *application) makeReport(w http.ResponseWriter, r *http.Request) {
	err := r.ParseForm()
	if err != nil {
		http.Error(w, "failed to parse form", http.StatusBadRequest)
		return
	}

	ranges := []string{"Items!A2:D", "Ingredients!A2:C"}
	resp, err := app.sheetsServices.Spreadsheets.Values.BatchGet(app.sheetID).Ranges(ranges...).Do()
	if err != nil {
		log.Fatalf("failed to read items or ingredients: %v", err)
	}

	// Get Items with ingredients
	items := make(map[string][]IngredientAmount)
	for _, row := range resp.ValueRanges[0].Values {
		if len(row) > 0 {
			item := fmt.Sprintf("%v", row[0])
			ingredient := fmt.Sprintf("%v", row[1])
			quantity := fmt.Sprintf("%v", row[2])
			unit := fmt.Sprintf("%v", row[3])
			items[item] = append(items[item], IngredientAmount{
				Name:     ingredient,
				Quantity: parseQuantity(quantity, unit),
			})
		}
	}

	// Get Ingredients with prices
	ingredientPrices := make(map[string]float64)
	ingredientUnits := make(map[string]string)
	for _, row := range resp.ValueRanges[1].Values {
		if len(row) > 0 {
			ingredient := fmt.Sprintf("%v", row[0])
			unit := fmt.Sprintf("%v", row[1])
			price := fmt.Sprintf("%v", row[2])
			pricefloat := parsePricePerSmallestUnit(price, unit)
			ingredientPrices[ingredient] = pricefloat
			ingredientUnits[ingredient] = unit
		}
	}

	currentDate := time.Now().Format("2006/01/02")

	// Calculate costs and build rows for sheets
	var itemRows [][]any
	ingredientCosts := make(map[string]IngredientCost)

	for itemName, values := range r.Form {
		count, _ := strconv.Atoi(values[0])
		if count == 0 {
			continue
		}

		totalCost := 0.0
		for _, ingredient := range items[itemName] {
			price := ingredientPrices[ingredient.Name]
			cost := round(float64(ingredient.Quantity) * price * float64(count))

			currentIngredientCost := ingredientCosts[ingredient.Name]
			currentIngredientCost.TotalSpend = round(currentIngredientCost.TotalSpend + cost)
			currentIngredientCost.Quantity += ingredient.Quantity * count
			ingredientCosts[ingredient.Name] = currentIngredientCost

			totalCost += cost
		}

		// Add row directly to itemRows
		itemRows = append(itemRows, []any{currentDate, itemName, count, round(totalCost)})
	}

	// Build ingredient rows
	var ingredientRows [][]any
	for ingredientName, ingredientCost := range ingredientCosts {
		originalQuantity := convertToOriginalUnit(ingredientCost.Quantity, ingredientUnits[ingredientName])
		ingredientRows = append(ingredientRows, []any{
			currentDate,
			ingredientName,
			originalQuantity,
			ingredientCost.TotalSpend,
		})
	}

	// Write to Order_Items sheet
	if len(itemRows) > 0 {
		itemRange := "Order Items!A:D"
		itemValueRange := &sheets.ValueRange{
			Values: itemRows,
		}
		_, err = app.sheetsServices.Spreadsheets.Values.Append(app.sheetID, itemRange, itemValueRange).
			ValueInputOption("RAW").Do()
		if err != nil {
			log.Printf("failed to write to Order_Items: %v", err)
			http.Error(w, "failed to write order items", http.StatusInternalServerError)
			return
		}
	}

	// Write to Order_Ingredients sheet
	if len(ingredientRows) > 0 {
		ingredientRange := "Order Ingredients!A:D"
		ingredientValueRange := &sheets.ValueRange{
			Values: ingredientRows,
		}
		_, err = app.sheetsServices.Spreadsheets.Values.Append(app.sheetID, ingredientRange, ingredientValueRange).
			ValueInputOption("RAW").Do()
		if err != nil {
			log.Printf("failed to write to Order_Ingredients: %v", err)
			http.Error(w, "failed to write order ingredients", http.StatusInternalServerError)
			return
		}
	}

	http.Redirect(w, r, "/reports", http.StatusSeeOther)

}

type DailyReport struct {
	Date       string
	TotalCost  float64
}

func (app *application) showReports(w http.ResponseWriter, r *http.Request) {
	// Read all data from Order Items sheet (skip header row)
	readRange := "Order Items!A2:D"
	resp, err := app.sheetsServices.Spreadsheets.Values.Get(app.sheetID, readRange).Do()
	if err != nil {
		log.Printf("failed to read order items: %v", err)
		http.Error(w, "failed to read order items", http.StatusInternalServerError)
		return
	}

	// Group by date and sum costs
	dailyTotals := make(map[string]float64)
	for _, row := range resp.Values {
		if len(row) >= 4 {
			date := fmt.Sprintf("%v", row[0])
			cost, _ := strconv.ParseFloat(fmt.Sprintf("%v", row[3]), 64)
			dailyTotals[date] += cost
		}
	}

	// Convert map to slice for template
	var reports []DailyReport
	for date, total := range dailyTotals {
		reports = append(reports, DailyReport{
			Date:      date,
			TotalCost: round(total),
		})
	}

	data := map[string]any{
		"Reports": reports,
	}
	app.render(w, http.StatusOK, "reports.html", data)
}
