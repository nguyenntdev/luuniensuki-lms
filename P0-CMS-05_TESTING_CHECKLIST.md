# P0-CMS-05: Content Tagging - Testing Checklist

## Pre-deployment Checklist

### 1. Database Migration
- [ ] Migration file `0013_content_tagging.py` created
- [ ] Migration runs successfully: `alembic upgrade head`
- [ ] Tables created: `tags`, `content_tags`
- [ ] All indexes created correctly
- [ ] Foreign key constraints in place
- [ ] Unique constraints working

### 2. Models
- [ ] `Tag` model defined in `backend/models.py`
- [ ] `ContentTag` model defined in `backend/models.py`
- [ ] `TagType` enum defined (topic, difficulty, audience, era, style)
- [ ] `ContentType` enum defined (lesson, motif, quiz, quest)
- [ ] Models imported in `backend/main.py`
- [ ] Relationships configured correctly

### 3. Schemas
- [ ] `TagOut` schema defined
- [ ] `TagCreateIn` schema defined
- [ ] `ContentTagOut` schema defined
- [ ] `ContentTagCreateIn` schema defined
- [ ] `SearchRequest` schema defined
- [ ] `SearchResponse` schema defined
- [ ] `SearchResultItem` schema defined

### 4. API Endpoints
- [ ] `GET /api/v1/tags` implemented
- [ ] `POST /api/v1/admin/tags` implemented
- [ ] `POST /api/v1/admin/content/{type}/{id}/tags` implemented
- [ ] `DELETE /api/v1/admin/content/{type}/{id}/tags/{slug}` implemented
- [ ] `GET /api/v1/search` implemented
- [ ] All endpoints follow existing patterns

### 5. Documentation
- [ ] Implementation summary created
- [ ] Quick reference guide created
- [ ] API reference created
- [ ] Testing guide included
- [ ] Usage examples provided

## Functional Testing

### Tag Management

#### Create Tag (Admin)
- [ ] Create topic tag successfully
- [ ] Create difficulty tag successfully
- [ ] Create audience tag successfully
- [ ] Create era tag successfully
- [ ] Create style tag successfully
- [ ] Duplicate slug returns 400 error
- [ ] Non-admin user returns 403 error
- [ ] Invalid tag_type returns 422 error
- [ ] Missing required fields returns 422 error

#### List Tags
- [ ] List all tags returns array
- [ ] Filter by tag_type works
- [ ] Only active tags returned
- [ ] Tags sorted by name
- [ ] No authentication required
- [ ] Empty database returns empty array

### Content Tagging

#### Add Tags to Content (Admin)
- [ ] Add tags to lesson successfully
- [ ] Add tags to motif successfully
- [ ] Add tags to quiz successfully
- [ ] Add tags to quest successfully
- [ ] Multiple tags can be added at once
- [ ] Returns all tags for content
- [ ] Duplicate tag addition is idempotent
- [ ] Non-existent content returns 404
- [ ] Non-existent tag returns 404
- [ ] Invalid content_type returns 400
- [ ] Non-admin user returns 403

#### Remove Tag from Content (Admin)
- [ ] Remove tag from lesson successfully
- [ ] Remove tag from motif successfully
- [ ] Remove tag from quiz successfully
- [ ] Remove tag from quest successfully
- [ ] Returns 204 on success
- [ ] Idempotent (removing twice is safe)
- [ ] Non-existent tag is safe (204)
- [ ] Invalid content_type returns 400
- [ ] Non-admin user returns 403

### Search Functionality

#### Search by Query
- [ ] Search lessons by text works
- [ ] Search motifs by text works
- [ ] Case-insensitive search works
- [ ] Partial match works
- [ ] Empty query returns all content
- [ ] No results returns empty array

#### Search by Tags
- [ ] Single tag filter works
- [ ] Multiple tag filter works (OR logic)
- [ ] Tag filter with content_type works
- [ ] Non-existent tag returns empty array
- [ ] Empty tag list returns all content

#### Combined Search
- [ ] Query + tags works
- [ ] Query + tags + content_types works
- [ ] Limit parameter works
- [ ] Results include tag information
- [ ] Relevance score populated

#### Edge Cases
- [ ] Limit=1 returns 1 result
- [ ] Limit=100 returns max 100 results
- [ ] Limit>100 is capped at 100
- [ ] Invalid content_type returns 400
- [ ] Special characters in query handled

## Integration Testing

### Database
- [ ] Tags persist correctly
- [ ] ContentTags persist correctly
- [ ] Cascade delete works (tag deletion removes content_tags)
- [ ] Unique constraint prevents duplicates
- [ ] Indexes improve query performance
- [ ] Transactions rollback on error

### Authentication
- [ ] Admin endpoints require auth token
- [ ] Public endpoints work without auth
- [ ] Invalid token returns 401
- [ ] Non-admin token returns 403
- [ ] Expired token returns 401

### Data Integrity
- [ ] Can't tag non-existent content
- [ ] Can't use non-existent tags
- [ ] Content deletion doesn't break tags
- [ ] Tag deactivation filters from search
- [ ] Foreign keys maintain referential integrity

## Performance Testing

### Query Performance
- [ ] List tags is fast (<100ms)
- [ ] Search with tags is fast (<200ms)
- [ ] Search with text query is fast (<300ms)
- [ ] Tag creation is fast (<100ms)
- [ ] Bulk tagging is efficient

### Load Testing
- [ ] Handle 100 concurrent searches
- [ ] Handle 1000 tags in database
- [ ] Handle 10000 content_tags
- [ ] No N+1 query problems
- [ ] Indexes are being used

### Scalability
- [ ] Pagination works for large result sets
- [ ] Search limit prevents memory issues
- [ ] Database queries are optimized
- [ ] Eager loading prevents extra queries

## Security Testing

### Authorization
- [ ] Only admins can create tags
- [ ] Only admins can tag content
- [ ] Only admins can remove tags
- [ ] Anyone can search/list tags
- [ ] Role checks are enforced

### Input Validation
- [ ] SQL injection prevented
- [ ] XSS in tag names prevented
- [ ] Invalid UUIDs rejected
- [ ] Long strings truncated/rejected
- [ ] Special characters handled safely

### Error Handling
- [ ] Errors return appropriate status codes
- [ ] Error messages don't leak sensitive info
- [ ] Database errors caught and logged
- [ ] Invalid input handled gracefully

## Documentation Testing

### API Documentation
- [ ] All endpoints documented
- [ ] Request/response examples provided
- [ ] Error codes documented
- [ ] Authentication requirements clear

### Code Documentation
- [ ] Models have docstrings
- [ ] Functions have docstrings
- [ ] Complex logic is commented
- [ ] Migration has description

### User Documentation
- [ ] Usage examples work
- [ ] Quick reference is accurate
- [ ] Testing guide is complete
- [ ] Troubleshooting helps debug

## Post-deployment Verification

### Production Checks
- [ ] Migration applied successfully
- [ ] No database errors in logs
- [ ] Initial tags seeded
- [ ] Search returns results
- [ ] Performance acceptable
- [ ] No 500 errors

### Monitoring
- [ ] API endpoints respond
- [ ] Response times reasonable
- [ ] No error spikes
- [ ] Database queries optimized
- [ ] Cache hit rate good (if caching)

### User Acceptance
- [ ] Admin can create tags
- [ ] Admin can tag content
- [ ] Users can search by tags
- [ ] Search results are relevant
- [ ] UI displays tags correctly

## Rollback Plan

If issues are found:

1. **Database rollback:**
   ```bash
   alembic downgrade -1
   ```

2. **Code rollback:**
   - Revert commits for models, endpoints
   - Remove migration file
   - Restart services

3. **Data cleanup:**
   - If partially migrated, clean up orphaned data
   - Verify foreign key integrity

## Sign-off

- [ ] All functional tests pass
- [ ] All integration tests pass
- [ ] Performance acceptable
- [ ] Security verified
- [ ] Documentation complete
- [ ] Production deployment successful
- [ ] Monitoring in place

**Tested by:** _________________  
**Date:** _________________  
**Approved by:** _________________  
**Date:** _________________

