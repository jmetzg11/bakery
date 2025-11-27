package main

import (
	"fmt"
	"log"
	"math"
	"net/http"
	"strconv"
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
	for _, row := range resp.ValueRanges[1].Values {
		if len(row) > 0 {
			ingredient := fmt.Sprintf("%v", row[0])
			unit := fmt.Sprintf("%v", row[1])
			price := fmt.Sprintf("%v", row[2])
			pricefloat := parsePricePerSmallestUnit(price, unit)
			ingredientPrices[ingredient] = pricefloat
		}
	}

	// Get price for each item
	itemCosts := make(map[string]ItemCost)
	for itemName, values := range r.Form {
		count, _ := strconv.Atoi(values[0])

		totalCost := 0.0
		for _, ingredient := range items[itemName] {
			price := ingredientPrices[ingredient.Name]
			cost := float64(ingredient.Quantity) * price
			totalCost += cost
		}
		itemCosts[itemName] = ItemCost{
			Count:      count,
			TotalSpent: math.Round(totalCost*float64(count)*100) / 100,
		}
	}

	http.Redirect(w, r, "/", http.StatusSeeOther)

}

func (app *application) showReports(w http.ResponseWriter, r *http.Request) {
	app.render(w, http.StatusOK, "reports.html", nil)
}
