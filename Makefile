run:
	@echo "Starting Go backend with hot reloading..."
	air

down:
	@echo "Stopping Go backend..."
	-pkill -f "tmp/main"
	@echo "Cleaning up Go build artifacts..."
	-rm -f tmp/main
	@echo "Stopped successfully!"

# run:
# 	@echo "Building Tailwind CSS..."
# 	npm run build:css
# 	@echo "Starting Go backend with hot reloading..."
# 	air

# down:
# 	@echo "Stopping Go backend..."
# 	-pkill -f "tmp/main"
# 	@echo "Cleaning up Go build artifacts..."
# 	-rm -f tmp/main
# 	@echo "Stopped successfully!"
