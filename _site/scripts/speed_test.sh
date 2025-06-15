#!/bin/bash

# 🚀 Jekyll Site Speed Testing Suite
# ==================================

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "🚀 JEKYLL SITE SPEED TESTING SUITE"
echo "=================================="
echo -e "${NC}"

# Controlla se Jekyll server è attivo
check_server() {
    echo -e "${YELLOW}📡 Checking Jekyll server...${NC}"
    
    if curl -s -f http://localhost:4000 > /dev/null; then
        echo -e "${GREEN}✅ Jekyll server is running on http://localhost:4000${NC}"
        return 0
    else
        echo -e "${RED}❌ Jekyll server not found on http://localhost:4000${NC}"
        echo -e "${YELLOW}💡 Start it with: bundle exec jekyll serve --host=0.0.0.0 --port=4000${NC}"
        return 1
    fi
}

# Test rapido
quick_test() {
    echo -e "\n${BLUE}⚡ Running Quick Speed Test...${NC}"
    python3 scripts/quick_speed_test.py
}

# Test completo
full_audit() {
    echo -e "\n${BLUE}🔍 Running Comprehensive Audit...${NC}"
    python3 scripts/comprehensive_speed_audit.py
}

# Menu principale
show_menu() {
    echo -e "\n${YELLOW}Choose test type:${NC}"
    echo "1) ⚡ Quick Test (30 seconds)"
    echo "2) 🔍 Full Audit (2-3 minutes)"
    echo "3) 🏃 Run Both"
    echo "4) 🚪 Exit"
    echo
}

# Main
main() {
    # Controlla server
    if ! check_server; then
        exit 1
    fi
    
    # Se argomento passato, esegui direttamente
    case "$1" in
        "quick"|"q")
            quick_test
            exit 0
            ;;
        "full"|"f")
            full_audit
            exit 0
            ;;
        "both"|"b")
            quick_test
            echo -e "\n${YELLOW}Waiting 3 seconds before full audit...${NC}"
            sleep 3
            full_audit
            exit 0
            ;;
    esac
    
    # Menu interattivo
    while true; do
        show_menu
        read -p "Select option [1-4]: " choice
        case $choice in
            1)
                quick_test
                ;;
            2)
                full_audit
                ;;
            3)
                quick_test
                echo -e "\n${YELLOW}Waiting 3 seconds before full audit...${NC}"
                sleep 3
                full_audit
                ;;
            4)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option. Please select 1-4.${NC}"
                ;;
        esac
        
        echo -e "\n${YELLOW}Press Enter to continue...${NC}"
        read
    done
}

# Esegui main con argomenti
main "$@"
