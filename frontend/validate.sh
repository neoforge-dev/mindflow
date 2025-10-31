#!/bin/bash
#
# MindFlow Landing Page Validation Script
#
# Validates HTML structure, accessibility, and performance
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================"
echo "MindFlow Landing Page Validator"
echo "================================"
echo ""

# Check if index.html exists
if [ ! -f "index.html" ]; then
    echo -e "${RED}✗ index.html not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ index.html found${NC}"

# Validate HTML structure
echo ""
echo "Checking HTML structure..."

# Check for required meta tags
if grep -q '<meta charset="UTF-8">' index.html; then
    echo -e "${GREEN}✓ Charset meta tag present${NC}"
else
    echo -e "${RED}✗ Missing charset meta tag${NC}"
fi

if grep -q '<meta name="viewport"' index.html; then
    echo -e "${GREEN}✓ Viewport meta tag present${NC}"
else
    echo -e "${RED}✗ Missing viewport meta tag${NC}"
fi

if grep -q '<meta name="description"' index.html; then
    echo -e "${GREEN}✓ Meta description present${NC}"
else
    echo -e "${RED}✗ Missing meta description${NC}"
fi

# Check for Open Graph tags
if grep -q 'property="og:title"' index.html; then
    echo -e "${GREEN}✓ Open Graph tags present${NC}"
else
    echo -e "${YELLOW}⚠ Missing Open Graph tags${NC}"
fi

# Check for Twitter Card tags
if grep -q 'name="twitter:card"' index.html; then
    echo -e "${GREEN}✓ Twitter Card tags present${NC}"
else
    echo -e "${YELLOW}⚠ Missing Twitter Card tags${NC}"
fi

# Check for semantic HTML
echo ""
echo "Checking semantic HTML..."

h1_count=$(grep -c '<h1' index.html || echo "0")
if [ "$h1_count" -eq 1 ]; then
    echo -e "${GREEN}✓ Single H1 tag (SEO best practice)${NC}"
else
    echo -e "${RED}✗ Found $h1_count H1 tags (should be 1)${NC}"
fi

if grep -q '<section' index.html; then
    echo -e "${GREEN}✓ Semantic sections present${NC}"
else
    echo -e "${YELLOW}⚠ No semantic sections found${NC}"
fi

if grep -q '<footer' index.html; then
    echo -e "${GREEN}✓ Footer element present${NC}"
else
    echo -e "${YELLOW}⚠ No footer element${NC}"
fi

# Check for performance optimizations
echo ""
echo "Checking performance optimizations..."

if grep -q 'preconnect' index.html; then
    echo -e "${GREEN}✓ Preconnect hints present${NC}"
else
    echo -e "${YELLOW}⚠ No preconnect hints${NC}"
fi

if grep -q 'defer' index.html; then
    echo -e "${GREEN}✓ Deferred JavaScript present${NC}"
else
    echo -e "${YELLOW}⚠ No deferred scripts${NC}"
fi

# Check for accessibility
echo ""
echo "Checking accessibility..."

if grep -q 'aria-hidden="true"' index.html; then
    echo -e "${GREEN}✓ ARIA attributes present${NC}"
else
    echo -e "${YELLOW}⚠ No ARIA attributes found${NC}"
fi

# Check for Alpine.js
if grep -q 'alpinejs' index.html; then
    echo -e "${GREEN}✓ Alpine.js included${NC}"
else
    echo -e "${RED}✗ Alpine.js not found${NC}"
fi

# Check for Tailwind CSS
if grep -q 'tailwindcss' index.html; then
    echo -e "${GREEN}✓ Tailwind CSS included${NC}"
else
    echo -e "${RED}✗ Tailwind CSS not found${NC}"
fi

# Check file size
echo ""
echo "Checking file size..."

file_size=$(wc -c < index.html)
file_size_kb=$((file_size / 1024))

if [ $file_size_kb -lt 50 ]; then
    echo -e "${GREEN}✓ File size: ${file_size_kb}KB (target: <50KB)${NC}"
elif [ $file_size_kb -lt 100 ]; then
    echo -e "${YELLOW}⚠ File size: ${file_size_kb}KB (target: <50KB)${NC}"
else
    echo -e "${RED}✗ File size: ${file_size_kb}KB (too large, target: <50KB)${NC}"
fi

# Check for Custom GPT links
echo ""
echo "Checking Custom GPT integration..."

cta_count=$(grep -c 'chatgpt.com/g/' index.html || echo "0")
if [ "$cta_count" -ge 2 ]; then
    echo -e "${GREEN}✓ Found $cta_count CTA links to Custom GPT${NC}"
else
    echo -e "${YELLOW}⚠ Found only $cta_count CTA link(s) (expected 2+)${NC}"
fi

# Check for analytics
echo ""
echo "Checking analytics integration..."

if grep -q 'simpleanalytics' index.html || grep -q 'plausible' index.html; then
    echo -e "${GREEN}✓ Privacy-friendly analytics present${NC}"
else
    echo -e "${YELLOW}⚠ No analytics found${NC}"
fi

# Summary
echo ""
echo "================================"
echo "Validation Complete"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Start local server: npm run dev"
echo "2. Open http://localhost:8000"
echo "3. Run Lighthouse: npm run lighthouse"
echo "4. Run Playwright tests: npm test"
echo ""
