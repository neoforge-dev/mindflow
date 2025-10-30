# Archived Documentation

**Date Archived**: 2025-10-30
**Reason**: Documentation consolidation - these files contained redundant/outdated information

---

## Files in This Archive

These files were consolidated into the new documentation structure:

### Archived Files

1. **architecture-1pager.md** - Old GAS-based architecture (superseded by ARCHITECTURE.md)
2. **build-plan-bootstrap.md** - GAS bootstrap plan (no longer relevant)
3. **custom-views-todoist-ui.md** - UI component examples (merged into IMPLEMENTATION.md)
4. **mindflow-checklist.md** - Checklists (merged into DEPLOYMENT.md)
5. **mindflow-spec.md** - Original spec (consolidated into ARCHITECTURE.md)
6. **mindflow-starter.md** - Code examples (merged into IMPLEMENTATION.md)
7. **mindflow-summary.md** - Executive summary (merged into PRODUCT.md)
8. **production-fastapi-lit.md** - FastAPI guide (merged into IMPLEMENTATION.md)
9. **turn-to-product.md** - Product planning (merged into PRODUCT.md)

### Why These Were Archived

**Problems with old structure**:
- **60-70% redundancy** across files
- **Mixed concerns** (architecture + implementation + business logic in single files)
- **GAS-focused content** no longer relevant (moving to FastAPI)
- **Difficult to navigate** (9 files, unclear hierarchy)
- **Context pollution** (~50,000 words loaded unnecessarily)

### New Structure

All useful content has been preserved and reorganized into:

- **ARCHITECTURE.md** - System design, tech decisions, data model
- **IMPLEMENTATION.md** - Copy-paste ready code, setup guide
- **DEPLOYMENT.md** - Docker, Fly.io, production deployment
- **PRODUCT.md** - Vision, roadmap, business model
- **README.md** - Navigation and quick reference

**Result**:
- Reduced from **~50,000 words** to **~15,000 words**
- Clear separation of concerns
- Single source of truth for each topic
- Zero duplication

---

## Need Something from the Old Docs?

**Check first**:
1. Search the new docs (likely already there)
2. If GAS-specific content needed, see this archive
3. If truly missing, file an issue: github.com/yourusername/mindflow/issues

---

## Restoration

If you need to restore any of these files:

```bash
# View archived files
ls /Users/bogdan/work/neoforge-dev/mindflow/docs/archive/

# Copy back to main docs
cp archive/filename.md ../filename.md
```

**Note**: Restoration not recommended - new docs are more complete and better organized.
