# Stage 1: Build the Go application
FROM golang:1.23 as builder

# Set the working directory inside the container
WORKDIR /app

# Copy the Go module files and download dependencies
COPY go.mod ./
RUN go mod download

# Copy the application source code
COPY . .

# Build the Go application with static linking
RUN CGO_ENABLED=0 GOOS=linux go build -a -o DQG .

# Stage 2: Create the final image
FROM alpine:latest

# Install necessary packages
RUN apk add --no-cache ca-certificates

# Set the working directory for the final image
WORKDIR /app

# Copy the built Go binary from the builder stage
COPY --from=builder /app/DQG /app/

# Copy the HTML file to serve
COPY index.html /app/

# Create an "outputs" directory for storing CSV files
RUN mkdir -p /app/outputs

# Ensure the binary has executable permissions
RUN chmod +x /app/DQG

# Expose the application port
EXPOSE 8002

# Set the entry point to the Go application
CMD ["./app/DQG"]