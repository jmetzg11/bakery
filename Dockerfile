# Build stage
FROM node:20-alpine AS node-builder

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci

# Copy static assets and build CSS
COPY ui ./ui
COPY tailwind.config.js ./
RUN npm run build:css

# Go build stage
FROM golang:1.25.1-alpine AS go-builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY *.go ./

# Copy built CSS from node-builder stage
COPY --from=node-builder /app/ui ./ui

# Build the Go binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Final stage
FROM alpine:latest

WORKDIR /app

# Install ca-certificates for HTTPS requests
RUN apk --no-cache add ca-certificates

# Copy the binary from builder
COPY --from=go-builder /app/main .

# Copy the ui directory (templates and static files)
COPY --from=go-builder /app/ui ./ui

# Expose port
EXPOSE 3000

# Run with prod flag
CMD ["./main", "-prod"]
