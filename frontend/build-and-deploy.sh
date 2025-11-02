#!/bin/bash
# Build frontend and deploy to backend assets directory
#
# This script:
# 1. Builds the React component using esbuild
# 2. Copies the compiled output to backend/mcp_server/assets/
# 3. Validates the deployment

set -e  # Exit on error

echo "🏗️  Building MindFlow ChatGPT Apps SDK component..."

# Change to frontend directory
cd "$(dirname "$0")"

# Run the build
npm run build

# Copy to backend assets
echo "📦 Deploying to backend assets..."
BACKEND_ASSETS="../backend/mcp_server/assets"
mkdir -p "$BACKEND_ASSETS"
cp dist/index.js "$BACKEND_ASSETS/taskcard.js"

# Verify deployment
if [ -f "$BACKEND_ASSETS/taskcard.js" ]; then
    SIZE=$(du -h "$BACKEND_ASSETS/taskcard.js" | cut -f1)
    echo "✅ Deployment successful!"
    echo "   Component size: $SIZE"
    echo "   Location: $BACKEND_ASSETS/taskcard.js"
else
    echo "❌ Deployment failed - file not found"
    exit 1
fi

echo ""
echo "🎉 Build and deployment complete!"
echo ""
echo "Next steps:"
echo "1. Start the backend: cd ../backend && uv run python -m mindflow.main"
echo "2. Start the MCP server: cd ../backend && uv run fastmcp run mcp_server.main:mcp"
echo "3. Test in ChatGPT with the 'get_next_task' tool"
