#!/bin/bash

# Maintenance script for Instagram Influencer Analyzer

function show_help {
    echo "Usage: $0 [command]"
    echo "Commands:"
    echo "  logs            - Show container logs"
    echo "  restart         - Restart all containers"
    echo "  stop            - Stop all containers"
    echo "  start           - Start all containers"
    echo "  rebuild         - Rebuild and restart containers"
    echo "  status          - Show container status"
    echo "  clean           - Clean unused Docker resources"
    echo "  update          - Pull latest code and restart"
    echo "  help            - Show this help message"
}

# Ensure we're in the correct directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

case "$1" in
    logs)
        echo "Showing logs (Ctrl+C to exit)..."
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    restart)
        echo "Restarting containers..."
        docker-compose -f docker-compose.prod.yml restart
        ;;
    stop)
        echo "Stopping containers..."
        docker-compose -f docker-compose.prod.yml down
        ;;
    start)
        echo "Starting containers..."
        docker-compose -f docker-compose.prod.yml up -d
        ;;
    rebuild)
        echo "Rebuilding and restarting containers..."
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up --build -d
        ;;
    status)
        echo "Container status:"
        docker-compose -f docker-compose.prod.yml ps
        ;;
    clean)
        echo "Cleaning Docker resources..."
        docker system prune -f
        ;;
    update)
        echo "Updating application..."
        git pull
        ./scripts/deploy.sh
        ;;
    *)
        show_help
        ;;
esac 