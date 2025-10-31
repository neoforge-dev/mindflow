# MindFlow Landing Page - Quick Start

**5-Minute Setup Guide**

## Local Testing (Now)

```bash
# 1. Navigate to frontend directory
cd /Users/bogdan/work/neoforge-dev/mindflow/frontend

# 2. Start local server (Python 3)
python3 -m http.server 8000

# 3. Open browser
open http://localhost:8000

# 4. Run validation
./validate.sh
```

**Expected Result**: All validation checks pass ✅

## Deploy to Production (10 Minutes)

### Option 1: Cloudflare Pages (Recommended)

**One-Time Setup**:
```bash
# 1. Install Wrangler CLI
npm install -g wrangler

# 2. Login to Cloudflare
wrangler login
```

**Deploy**:
```bash
cd /Users/bogdan/work/neoforge-dev/mindflow/frontend
wrangler pages publish . --project-name=mindflow
```

**Result**: Live at `https://mindflow.pages.dev` in <2 minutes

### Option 2: Vercel (Fastest)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
cd /Users/bogdan/work/neoforge-dev/mindflow/frontend
vercel --prod
```

**Result**: Live at custom URL in <1 minute

### Option 3: Netlify Drop (No CLI)

1. Visit [app.netlify.com/drop](https://app.netlify.com/drop)
2. Drag and drop `frontend` folder
3. Done!

**Result**: Live at custom URL instantly

## Pre-Deployment Checklist (2 Minutes)

```bash
cd /Users/bogdan/work/neoforge-dev/mindflow/frontend

# Run validation
./validate.sh

# Expected output:
# ✓ index.html found
# ✓ All meta tags present
# ✓ Single H1 tag
# ✓ File size: 17KB
# ✓ 2 CTA links
```

**Critical Items**:
- [ ] Custom GPT link updated (line 115 and 385 in index.html)
- [ ] GitHub username updated (replace `yourusername`)
- [ ] Twitter handle updated (replace `@yourusername`)
- [ ] Email verified (`hello@mindflow.ai`)

## Update Custom GPT Link

```bash
# Open index.html
code index.html  # or vim, nano, etc.

# Find and replace (2 occurrences):
# FROM: href="https://chatgpt.com/g/g-69035fdcdd648191807929b189684451-mindflow"
# TO:   href="https://chatgpt.com/g/g-YOUR-CUSTOM-GPT-ID"
```

**Lines to update**:
- Line ~115 (Hero CTA)
- Line ~385 (Final CTA)

## Test Locally (5 Minutes)

### Manual Testing

```bash
# 1. Start server
python3 -m http.server 8000

# 2. Open browser
open http://localhost:8000

# 3. Check:
- [ ] Hero headline visible
- [ ] CTA button clickable
- [ ] Demo animation plays
- [ ] All sections render
- [ ] Mobile responsive (resize window)
- [ ] No console errors (F12 → Console)
```

### Automated Testing (Optional)

```bash
# Install Playwright (first time only)
npm install

# Run tests
npm test

# Expected: 40+ tests pass
```

### Performance Audit (Optional)

```bash
# Install Lighthouse (first time only)
npm install -g lighthouse

# Run audit
npm run lighthouse

# Expected: All scores >90
```

## Deploy with Custom Domain (5 Minutes)

### Cloudflare Pages

1. **Deploy** (see above)
2. **Add domain**:
   - Cloudflare Pages dashboard → Custom domains
   - Add `mindflow.ai`
   - Add DNS records (automatic)
3. **Wait for SSL** (1-5 minutes)
4. **Test**: https://mindflow.ai

### Vercel

```bash
# After deploying
vercel domains add mindflow.ai
vercel domains verify mindflow.ai
```

## Post-Deployment Verification (2 Minutes)

```bash
# Test live site
curl -I https://mindflow.ai

# Expected:
# HTTP/2 200
# content-type: text/html
# x-frame-options: DENY
```

**Manual Checks**:
- [ ] Visit https://mindflow.ai
- [ ] Page loads in <2 seconds
- [ ] Click hero CTA → opens Custom GPT
- [ ] Test on mobile device
- [ ] No console errors

## Analytics Setup (3 Minutes)

### Simple Analytics (Recommended)

1. **Sign up**: [simpleanalytics.com](https://simpleanalytics.com/)
2. **Add domain**: `mindflow.ai`
3. **Verify**: Script already in `index.html`
4. **Test**: Visit site, check dashboard

**Already configured** - no code changes needed!

### Alternative: Plausible

```bash
# Replace analytics script in index.html
# Line ~460

# FROM:
<script async defer src="https://scripts.simpleanalyticscdn.com/latest.js"></script>

# TO:
<script defer data-domain="mindflow.ai" src="https://plausible.io/js/script.js"></script>
```

## Troubleshooting

### Issue: Page doesn't load locally

```bash
# Try alternative server
npx http-server -p 8000 -c-1
```

### Issue: Tailwind CSS not showing

**Check**:
1. Internet connection active
2. CDN script in `<head>`
3. No ad blockers

**Fix**:
```html
<!-- Use unpkg CDN as fallback -->
<script src="https://unpkg.com/tailwindcss@3/dist/tailwind.min.js"></script>
```

### Issue: Alpine.js demo not working

**Check**:
1. `defer` attribute on script
2. No JavaScript errors in console

**Debug**:
```javascript
// Add to browser console
console.log('Alpine:', window.Alpine);
```

### Issue: Mobile layout broken

**Check**:
1. Viewport meta tag present
2. Test on actual device (not just DevTools)

**Verify**:
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

## Common Commands

```bash
# Development
npm run dev              # Start local server (Python)
npm run dev:node         # Start local server (Node.js)
npm run dev:live         # Start with live reload

# Testing
npm test                 # Run Playwright tests
npm run test:ui          # Playwright UI mode
./validate.sh            # Quick validation

# Performance
npm run lighthouse       # Lighthouse audit
npm run lighthouse:ci    # Lighthouse CI mode

# Deployment
npm run deploy:cloudflare  # Deploy to Cloudflare
npm run deploy:vercel      # Deploy to Vercel
npm run deploy:netlify     # Deploy to Netlify
```

## File Locations

```
frontend/
├── index.html                      # Main landing page
├── README.md                       # Full documentation
├── DEPLOYMENT-CHECKLIST.md         # Production checklist
├── IMPLEMENTATION-SUMMARY.md       # Technical details
├── QUICKSTART.md                   # This file
├── package.json                    # Dev dependencies
└── validate.sh                     # Validation script
```

## Next Steps

### Before Launch
1. [ ] Update Custom GPT link
2. [ ] Update GitHub/Twitter usernames
3. [ ] Create visual assets (OG image, favicon)
4. [ ] Run `./validate.sh` - all checks pass
5. [ ] Deploy to Cloudflare Pages
6. [ ] Configure custom domain
7. [ ] Verify SSL certificate
8. [ ] Test on mobile device

### After Launch
1. [ ] Share on Twitter
2. [ ] Post to ProductHunt
3. [ ] Submit to Google Search Console
4. [ ] Monitor analytics
5. [ ] Collect user feedback

## Support

**Documentation**: See `README.md` for full details
**Issues**: GitHub Issues
**Questions**: hello@mindflow.ai

---

**Quick Links**:
- [Full Documentation](./README.md)
- [Deployment Checklist](./DEPLOYMENT-CHECKLIST.md)
- [Implementation Summary](./IMPLEMENTATION-SUMMARY.md)

**Estimated Time**:
- Local testing: 5 minutes
- Deploy to production: 10 minutes
- Custom domain setup: 5 minutes
- **Total: 20 minutes to live site** ⚡
