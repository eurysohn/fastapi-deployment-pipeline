#!/bin/bash
# =============================================================================
# Version Bump Script
# =============================================================================
# Bumps the version number in VERSION file and creates a git tag
#
# Usage:
#   ./scripts/bump-version.sh patch   # 1.0.0 -> 1.0.1
#   ./scripts/bump-version.sh minor   # 1.0.0 -> 1.1.0
#   ./scripts/bump-version.sh major   # 1.0.0 -> 2.0.0
#   ./scripts/bump-version.sh 1.2.3   # Set specific version
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
VERSION_FILE="VERSION"
APP_INIT_FILE="app/__init__.py"

# Get current version
get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | tr -d '[:space:]'
    else
        echo "0.0.0"
    fi
}

# Parse version components
parse_version() {
    local version=$1
    IFS='.' read -r major minor patch <<< "$version"
    echo "$major $minor $patch"
}

# Bump version based on type
bump_version() {
    local current=$1
    local bump_type=$2
    
    read major minor patch <<< $(parse_version "$current")
    
    case $bump_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            # Assume it's a specific version
            if [[ $bump_type =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo "$bump_type"
                return
            else
                echo -e "${RED}Error: Invalid version format. Use major, minor, patch, or X.Y.Z${NC}"
                exit 1
            fi
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Update version in files
update_version_files() {
    local new_version=$1
    
    # Update VERSION file
    echo "$new_version" > "$VERSION_FILE"
    echo -e "${GREEN}Updated $VERSION_FILE to $new_version${NC}"
    
    # Update app/__init__.py
    if [ -f "$APP_INIT_FILE" ]; then
        sed -i.bak "s/__version__ = \".*\"/__version__ = \"$new_version\"/" "$APP_INIT_FILE"
        rm -f "${APP_INIT_FILE}.bak"
        echo -e "${GREEN}Updated $APP_INIT_FILE to $new_version${NC}"
    fi
}

# Create git tag
create_git_tag() {
    local version=$1
    local tag="v$version"
    
    echo -e "${YELLOW}Creating git tag: $tag${NC}"
    
    # Check if tag already exists
    if git rev-parse "$tag" >/dev/null 2>&1; then
        echo -e "${RED}Error: Tag $tag already exists${NC}"
        exit 1
    fi
    
    # Stage version files
    git add "$VERSION_FILE" "$APP_INIT_FILE" 2>/dev/null || git add "$VERSION_FILE"
    
    # Commit
    git commit -m "chore: bump version to $version"
    
    # Create annotated tag
    git tag -a "$tag" -m "Release $version"
    
    echo -e "${GREEN}Created tag: $tag${NC}"
    echo -e "${YELLOW}Don't forget to push: git push origin main --tags${NC}"
}

# Main
main() {
    local bump_type=${1:-patch}
    
    echo "=========================================="
    echo "  Version Bump Script"
    echo "=========================================="
    echo ""
    
    # Get current version
    local current_version=$(get_current_version)
    echo -e "Current version: ${YELLOW}$current_version${NC}"
    
    # Calculate new version
    local new_version=$(bump_version "$current_version" "$bump_type")
    echo -e "New version:     ${GREEN}$new_version${NC}"
    echo ""
    
    # Confirm
    read -p "Proceed with version bump? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        update_version_files "$new_version"
        
        # Ask about git tag
        read -p "Create git tag? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            create_git_tag "$new_version"
        fi
        
        echo ""
        echo -e "${GREEN}Version bump complete!${NC}"
    else
        echo -e "${YELLOW}Cancelled${NC}"
    fi
}

# Show help
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 [major|minor|patch|X.Y.Z]"
    echo ""
    echo "Examples:"
    echo "  $0 patch   # 1.0.0 -> 1.0.1"
    echo "  $0 minor   # 1.0.0 -> 1.1.0"
    echo "  $0 major   # 1.0.0 -> 2.0.0"
    echo "  $0 2.0.0   # Set to 2.0.0"
    exit 0
fi

main "$@"
