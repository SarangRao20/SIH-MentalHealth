#!/bin/bash

# ==============================================================================
# 🚀 Complete Project Management Script - MindCare Mental Health App
# ==============================================================================
# Usage: ./run_project.sh [command]
# Commands:
#   setup      - Install dependencies and setup project
#   run        - Start the Flask development server
#   prod       - Start production server with gunicorn
#   dev        - Development mode with auto-reload
#   translate  - Run translation workflow
#   clean      - Clean cache and temp files
#   reset      - Reset database and restart
#   help       - Show this help
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_DIR="$(pwd)"
APP_FILE="app.py"
MAIN_FILE="main.py"
REQUIREMENTS_FILE="requirements.txt"
DB_FILE="instance/mental_health.db"
VENV_NAME="venv"
DEFAULT_PORT="8005"

# ==============================================================================
# Helper Functions
# ==============================================================================

print_banner() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${CYAN}🧠 MindCare Mental Health App Manager${NC}"
    echo -e "${PURPLE}🚀 Complete Project Management Solution${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_step() {
    echo -e "${YELLOW}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_python() {
    print_step "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        print_error "Python not found! Please install Python 3.8+"
        exit 1
    fi
    
    # Get Python version
    local python_cmd="python3"
    if ! command -v python3 &> /dev/null; then
        python_cmd="python"
    fi
    
    local python_version=$($python_cmd --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
    print_success "Python $python_version found"
    echo "$python_cmd"
}

check_project_files() {
    print_step "Checking project files..."
    
    local missing_files=()
    
    if [ ! -f "$APP_FILE" ] && [ ! -f "$MAIN_FILE" ]; then
        missing_files+=("app.py or main.py")
    fi
    
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        missing_files+=("requirements.txt")
    fi
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        print_error "Missing required files: ${missing_files[*]}"
        exit 1
    fi
    
    print_success "Project files check passed"
}

# ==============================================================================
# Project Management Functions
# ==============================================================================

setup_project() {
    print_step "Setting up project..."
    
    local python_cmd=$(check_python)
    check_project_files
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_NAME" ]; then
        print_info "Creating virtual environment..."
        $python_cmd -m venv "$VENV_NAME"
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source "$VENV_NAME/bin/activate" 2>/dev/null || source "$VENV_NAME/Scripts/activate" 2>/dev/null || {
        print_error "Failed to activate virtual environment"
        exit 1
    }
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install dependencies
    print_info "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
    
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
    
    # Create instance directory if it doesn't exist
    if [ ! -d "instance" ]; then
        mkdir -p instance
        print_info "Created instance directory"
    fi
    
    print_success "Project setup completed!"
}

start_development_server() {
    print_step "Starting development server..."
    
    local python_cmd=$(check_python)
    check_project_files
    
    # Activate virtual environment if it exists
    if [ -d "$VENV_NAME" ]; then
        source "$VENV_NAME/bin/activate" 2>/dev/null || source "$VENV_NAME/Scripts/activate" 2>/dev/null
    fi
    
    # Determine main file to run
    local main_file="$APP_FILE"
    if [ ! -f "$APP_FILE" ] && [ -f "$MAIN_FILE" ]; then
        main_file="$MAIN_FILE"
    fi
    
    print_info "Starting Flask server from $main_file..."
    print_info "Server will be available at: http://localhost:$DEFAULT_PORT"
    print_info "Press Ctrl+C to stop the server"
    echo -e "${YELLOW}============================================${NC}"
    
    # Set development environment
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    # Start the server
    $python_cmd "$main_file"
}

start_production_server() {
    print_step "Starting production server with Gunicorn..."
    
    # Check if gunicorn is installed
    if ! command -v gunicorn &> /dev/null; then
        print_info "Installing gunicorn..."
        pip install gunicorn
    fi
    
    # Activate virtual environment if it exists
    if [ -d "$VENV_NAME" ]; then
        source "$VENV_NAME/bin/activate" 2>/dev/null || source "$VENV_NAME/Scripts/activate" 2>/dev/null
    fi
    
    local app_module="app:app"
    if [ ! -f "$APP_FILE" ] && [ -f "$MAIN_FILE" ]; then
        app_module="main:app"
    fi
    
    print_info "Starting Gunicorn server..."
    print_info "Server will be available at: http://localhost:$DEFAULT_PORT"
    print_info "Press Ctrl+C to stop the server"
    echo -e "${YELLOW}============================================${NC}"
    
    gunicorn --bind 0.0.0.0:$DEFAULT_PORT --workers 4 "$app_module"
}

clean_project() {
    print_step "Cleaning project files..."
    
    local cleaned=0
    
    # Clean Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    cleaned=$((cleaned + 1))
    print_info "Cleaned Python cache files"
    
    # Clean Flask cache
    if [ -d ".flask_session" ]; then
        rm -rf .flask_session
        cleaned=$((cleaned + 1))
        print_info "Cleaned Flask session files"
    fi
    
    # Clean logs
    find . -name "*.log" -delete 2>/dev/null || true
    cleaned=$((cleaned + 1))
    print_info "Cleaned log files"
    
    # Clean temporary files
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*~" -delete 2>/dev/null || true
    cleaned=$((cleaned + 1))
    print_info "Cleaned temporary files"
    
    print_success "Cleaned $cleaned file types"
}

reset_database() {
    print_step "Resetting database..."
    
    if [ -f "$DB_FILE" ]; then
        echo -e "${YELLOW}This will delete all data. Are you sure? (y/N):${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -f "$DB_FILE"
            print_success "Database reset completed"
            print_info "Database will be recreated on next server start"
        else
            print_info "Database reset cancelled"
        fi
    else
        print_info "No database file found"
    fi
}

run_quick_translation() {
    print_step "Running quick translation setup..."
    
    # Create minimal babel.cfg if needed
    if [ ! -f "babel.cfg" ]; then
        cat > "babel.cfg" << EOF
[python: **.py]
[jinja2: **/templates/**.html]
EOF
        print_info "Created babel.cfg"
    fi
    
    # Check if pybabel is available
    if command -v pybabel &> /dev/null; then
        pybabel extract -F babel.cfg -o messages.pot . 2>/dev/null || true
        pybabel compile -d translations 2>/dev/null || true
        print_success "Translations compiled"
    else
        print_info "pybabel not found, skipping translations"
    fi
}

show_project_status() {
    print_step "Project Status"
    
    echo -e "${CYAN}📁 Project Directory:${NC} $PROJECT_DIR"
    
    # Check main files
    if [ -f "$APP_FILE" ]; then
        echo -e "${GREEN}✅ app.py found${NC}"
    elif [ -f "$MAIN_FILE" ]; then
        echo -e "${GREEN}✅ main.py found${NC}"
    else
        echo -e "${RED}❌ No main application file found${NC}"
    fi
    
    # Check requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${GREEN}✅ requirements.txt found${NC}"
    else
        echo -e "${RED}❌ requirements.txt not found${NC}"
    fi
    
    # Check virtual environment
    if [ -d "$VENV_NAME" ]; then
        echo -e "${GREEN}✅ Virtual environment exists${NC}"
    else
        echo -e "${YELLOW}⚠️  No virtual environment found${NC}"
    fi
    
    # Check database
    if [ -f "$DB_FILE" ]; then
        local db_size=$(du -h "$DB_FILE" | cut -f1)
        echo -e "${GREEN}✅ Database exists${NC} ($db_size)"
    else
        echo -e "${YELLOW}⚠️  No database found${NC}"
    fi
    
    # Check if server is running
    if lsof -i :$DEFAULT_PORT &> /dev/null; then
        echo -e "${GREEN}✅ Server running on port $DEFAULT_PORT${NC}"
    else
        echo -e "${BLUE}ℹ️  Server not running${NC}"
    fi
}

extract_messages() {
    print_step "Extracting translatable messages..."
    
    pybabel extract -F "$BABEL_CONFIG" -k _l -o "$POT_FILE" .
    
    if [ $? -eq 0 ]; then
        print_success "Messages extracted to $POT_FILE"
        
        # Show statistics
        if [ -f "$POT_FILE" ]; then
            local msg_count=$(grep -c "^msgid" "$POT_FILE" 2>/dev/null || echo "0")
            print_info "Found $msg_count translatable messages"
        fi
    else
        print_error "Failed to extract messages"
        exit 1
    fi
}

init_language() {
    local lang_code="$1"
    
    if [ -z "$lang_code" ]; then
        echo -e "${YELLOW}Enter language code (e.g., hi for Hindi, es for Spanish):${NC}"
        read -r lang_code
    fi
    
    if [ -z "$lang_code" ]; then
        print_error "Language code required"
        exit 1
    fi
    
    print_step "Initializing language: $lang_code"
    
    if [ ! -f "$POT_FILE" ]; then
        print_info "No messages.pot found, extracting first..."
        extract_messages
    fi
    
    pybabel init -i "$POT_FILE" -d "$TRANSLATIONS_DIR" -l "$lang_code"
    
    if [ $? -eq 0 ]; then
        print_success "Initialized language: $lang_code"
        print_info "Translation file created at: $TRANSLATIONS_DIR/$lang_code/LC_MESSAGES/messages.po"
    else
        print_error "Failed to initialize language: $lang_code"
        exit 1
    fi
}

update_translations() {
    print_step "Updating existing translations..."
    
    if [ ! -f "$POT_FILE" ]; then
        print_info "No messages.pot found, extracting first..."
        extract_messages
    fi
    
    pybabel update -i "$POT_FILE" -d "$TRANSLATIONS_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Translations updated"
        
        # Show language statistics
        for po_file in "$TRANSLATIONS_DIR"/*/LC_MESSAGES/messages.po; do
            if [ -f "$po_file" ]; then
                local lang=$(basename "$(dirname "$(dirname "$po_file")")")
                local total=$(grep -c "^msgid" "$po_file" 2>/dev/null || echo "0")
                local translated=$(grep -c "^msgstr \"[^\"]\+\"" "$po_file" 2>/dev/null || echo "0")
                local percentage=$((translated * 100 / total))
                print_info "$lang: $translated/$total messages translated (${percentage}%)"
            fi
        done
    else
        print_error "Failed to update translations"
        exit 1
    fi
}

compile_translations() {
    print_step "Compiling translations..."
    
    pybabel compile -d "$TRANSLATIONS_DIR"
    
    if [ $? -eq 0 ]; then
        print_success "Translations compiled successfully"
        
        # Show compiled files
        for mo_file in "$TRANSLATIONS_DIR"/*/LC_MESSAGES/messages.mo; do
            if [ -f "$mo_file" ]; then
                local lang=$(basename "$(dirname "$(dirname "$mo_file")")")
                local size=$(du -h "$mo_file" | cut -f1)
                print_info "Compiled $lang translation ($size)"
            fi
        done
    else
        print_error "Failed to compile translations"
        exit 1
    fi
}

auto_translate_hindi() {
    print_step "Applying automatic Hindi translations..."
    
    local po_file="$TRANSLATIONS_DIR/hi/LC_MESSAGES/messages.po"
    
    if [ ! -f "$po_file" ]; then
        print_error "Hindi translation file not found. Run init first."
        return 1
    fi
    
    # Create a temporary Python script for auto-translation
    cat > temp_translate.py << 'EOF'
import re
import sys

# Common Hindi translations
translations = {
    "Dashboard": "डैशबोर्ड",
    "Login": "लॉगिन",
    "Register": "पंजीकरण", 
    "Logout": "लॉगआउट",
    "Profile": "प्रोफाइल",
    "Settings": "सेटिंग्स",
    "Home": "होम",
    "Mental Health": "मानसिक स्वास्थ्य",
    "Assessment": "मूल्यांकन",
    "Meditation": "ध्यान",
    "Chat": "चैट",
    "Help": "मदद",
    "Submit": "जमा करें",
    "Cancel": "रद्द करें",
    "Save": "सेव करें",
    "Delete": "डिलीट करें",
    "Edit": "एडिट करें",
    "Search": "खोजें",
    "Welcome": "स्वागत है",
    "Loading": "लोड हो रहा है",
    "Success": "सफलता",
    "Error": "त्रुटि",
    "Warning": "चेतावनी"
}

def update_po_file(po_path):
    try:
        with open(po_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated = 0
        for english, hindi in translations.items():
            # Pattern to find empty msgstr for specific msgid
            pattern = rf'(msgid "{re.escape(english)}"\s*\nmsgstr ")("")'
            if re.search(pattern, content):
                content = re.sub(pattern, rf'\g<1>{hindi}\g<2>', content)
                updated += 1
        
        with open(po_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated {updated} translations")
        return updated > 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    po_file = sys.argv[1] if len(sys.argv) > 1 else "translations/hi/LC_MESSAGES/messages.po"
    success = update_po_file(po_file)
    sys.exit(0 if success else 1)
EOF

    python temp_translate.py "$po_file"
    local result=$?
    rm -f temp_translate.py
    
    if [ $result -eq 0 ]; then
        print_success "Applied automatic Hindi translations"
    else
        print_error "Failed to apply automatic translations"
    fi
    
    return $result
}

full_workflow() {
    print_step "Running complete translation workflow..."
    
    extract_messages
    
    # Check if Hindi translation exists, if not initialize it
    if [ ! -f "$TRANSLATIONS_DIR/hi/LC_MESSAGES/messages.po" ]; then
        print_info "Hindi translation not found, initializing..."
        init_language "hi"
    fi
    
    update_translations
    auto_translate_hindi
    compile_translations
    
    print_success "Complete translation workflow finished!"
}

clean_files() {
    print_step "Cleaning generated files..."
    
    local files_to_clean=("$POT_FILE" "temp_translate.py")
    local cleaned=0
    
    for file in "${files_to_clean[@]}"; do
        if [ -f "$file" ]; then
            rm -f "$file"
            print_info "Removed $file"
            ((cleaned++))
        fi
    done
    
    # Clean compiled .mo files if requested
    echo -e "${YELLOW}Remove compiled .mo files? (y/n):${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        find "$TRANSLATIONS_DIR" -name "*.mo" -delete 2>/dev/null || true
        print_info "Removed compiled translation files"
        ((cleaned++))
    fi
    
    print_success "Cleaned $cleaned files"
}

show_status() {
    print_step "Translation Status"
    
    if [ ! -d "$TRANSLATIONS_DIR" ]; then
        print_info "No translations directory found"
        return
    fi
    
    for lang_dir in "$TRANSLATIONS_DIR"/*; do
        if [ -d "$lang_dir" ]; then
            local lang=$(basename "$lang_dir")
            local po_file="$lang_dir/LC_MESSAGES/messages.po"
            local mo_file="$lang_dir/LC_MESSAGES/messages.mo"
            
            if [ -f "$po_file" ]; then
                local total=$(grep -c "^msgid" "$po_file" 2>/dev/null || echo "0")
                local translated=$(grep -c "^msgstr \"[^\"]\+\"" "$po_file" 2>/dev/null || echo "0")
                local percentage=$((total > 0 ? translated * 100 / total : 0))
                local compiled_status="❌"
                
                if [ -f "$mo_file" ]; then
                    compiled_status="✅"
                fi
                
                echo -e "${CYAN}$lang:${NC} $translated/$total (${percentage}%) | Compiled: $compiled_status"
            fi
        fi
    done
}

show_help() {
    echo -e "${CYAN}Usage: $0 [command]${NC}"
    echo ""
    echo -e "${YELLOW}Project Management:${NC}"
    echo -e "  ${GREEN}setup${NC}       Install dependencies and setup project"
    echo -e "  ${GREEN}run${NC}         Start Flask development server"
    echo -e "  ${GREEN}dev${NC}         Start in development mode"
    echo -e "  ${GREEN}prod${NC}        Start production server with Gunicorn"
    echo -e "  ${GREEN}status${NC}      Show project status"
    echo -e "  ${GREEN}clean${NC}       Clean cache and temporary files"
    echo -e "  ${GREEN}reset${NC}       Reset database"
    echo -e "  ${GREEN}translate${NC}   Setup translations"
    echo -e "  ${GREEN}help${NC}        Show this help"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo -e "  ${CYAN}$0 setup${NC}              # First time setup"
    echo -e "  ${CYAN}$0 run${NC}                # Start development server"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 setup                   # Setup project with dependencies"
    echo -e "  $0 run                     # Start development server"
    echo -e "  $0 prod                    # Start production server"
    echo -e "  $0 clean                   # Clean cache files"
    echo -e "  $0 reset                   # Reset database"
}

# ==============================================================================
# Main Script Logic
# ==============================================================================

main() {
    print_banner
    
    local command="${1:-run}"
    
    case "$command" in
        "setup")
            setup_project
            ;;
        "run"|"dev")
            start_development_server
            ;;
        "prod"|"production")
            start_production_server
            ;;
        "status")
            show_project_status
            ;;
        "clean")
            clean_project
            ;;
        "reset")
            reset_database
            ;;
        "translate")
            run_quick_translation
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
    
    if [ "$command" != "run" ] && [ "$command" != "dev" ] && [ "$command" != "prod" ]; then
        echo -e "${BLUE}================================================${NC}"
        echo -e "${GREEN}🎉 Command completed successfully!${NC}"
        echo -e "${BLUE}================================================${NC}"
    fi
}

# Run main function with all arguments
main "$@"