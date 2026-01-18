# P1-REC-01: Frontend Integration Guide

## Overview

This guide shows how to integrate the recommendation engine into the frontend/mobile applications.

## API Client Functions

### JavaScript/React (Web Frontend)

Add to `frontend/src/lib/api.js`:

```javascript
// =============================================================================
// Recommendation API
// =============================================================================

/**
 * Get personalized recommendations
 * @param {Object} options
 * @param {string} options.token - Auth token
 * @param {string} options.recommendationType - Optional type filter
 * @param {number} options.limit - Max results per type
 */
export function getRecommendations({ token, recommendationType, limit = 10 }) {
  const params = new URLSearchParams();
  if (recommendationType) params.append('recommendation_type', recommendationType);
  params.append('limit', limit.toString());
  
  return apiRequest(`/api/v1/recommendations?${params}`, { token });
}

/**
 * Get similar content
 */
export function getSimilarContent({ contentType, contentId, limit = 10, token }) {
  return apiRequest(
    `/api/v1/recommendations/similar/${contentType}/${contentId}?limit=${limit}`,
    { token }
  );
}

/**
 * Record content interaction
 */
export function recordInteraction({
  contentType,
  contentId,
  interactionType,
  durationSeconds = null,
  metadata = null,
  token
}) {
  return apiRequest('/api/v1/recommendations/interaction', {
    method: 'POST',
    token,
    body: {
      content_type: contentType,
      content_id: contentId,
      interaction_type: interactionType,
      duration_seconds: durationSeconds,
      metadata
    }
  });
}

/**
 * Submit recommendation feedback
 */
export function submitRecommendationFeedback({
  contentId,
  contentType,
  feedbackType,
  metadata = null,
  token
}) {
  return apiRequest('/api/v1/recommendations/feedback', {
    method: 'POST',
    token,
    body: {
      content_id: contentId,
      content_type: contentType,
      feedback_type: feedbackType,
      metadata
    }
  });
}
```

## React Components

### RecommendationsSection Component

```javascript
// components/RecommendationsSection.jsx
import { useState, useEffect } from 'react';
import { getRecommendations } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function RecommendationsSection() {
  const { token } = useAuth();
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRecommendations() {
      try {
        const data = await getRecommendations({ token, limit: 5 });
        setRecommendations(data);
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      } finally {
        setLoading(false);
      }
    }

    if (token) {
      fetchRecommendations();
    }
  }, [token]);

  if (loading) return <LoadingSpinner />;
  if (!recommendations) return null;

  return (
    <div className="recommendations">
      {/* Continue Learning */}
      {recommendations.continue_learning?.length > 0 && (
        <Section
          title="Continue Learning"
          items={recommendations.continue_learning}
          icon="📚"
        />
      )}

      {/* Discover New */}
      {recommendations.discover_new?.length > 0 && (
        <Section
          title="Discover New"
          items={recommendations.discover_new}
          icon="🌟"
        />
      )}

      {/* Review Needed */}
      {recommendations.review_needed?.length > 0 && (
        <Section
          title="Review These"
          items={recommendations.review_needed}
          icon="🔄"
        />
      )}

      {/* Popular */}
      {recommendations.popular?.length > 0 && (
        <Section
          title="Trending Now"
          items={recommendations.popular}
          icon="🔥"
        />
      )}
    </div>
  );
}

function Section({ title, items, icon }) {
  return (
    <div className="recommendation-section">
      <h2>
        <span className="icon">{icon}</span>
        {title}
      </h2>
      <div className="items-grid">
        {items.map(item => (
          <RecommendationCard key={item.content_id} item={item} />
        ))}
      </div>
    </div>
  );
}
```

### RecommendationCard Component

```javascript
// components/RecommendationCard.jsx
import { recordInteraction } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/router';

export default function RecommendationCard({ item }) {
  const { token } = useAuth();
  const router = useRouter();

  const handleClick = async () => {
    // Record view interaction
    await recordInteraction({
      contentType: item.content_type,
      contentId: item.content_id,
      interactionType: 'view',
      metadata: { source: 'recommendation', reason: item.reason },
      token
    });

    // Navigate to content
    if (item.content_type === 'motif') {
      router.push(`/motifs/${item.content_id}`);
    } else if (item.content_type === 'lesson') {
      router.push(`/lessons/${item.content_id}`);
    }
  };

  return (
    <div className="recommendation-card" onClick={handleClick}>
      <div className="content">
        <h3>{item.title}</h3>
        <p>{item.description}</p>
        
        {item.status && (
          <span className="status-badge">{item.status}</span>
        )}
        
        {item.similarity_score && (
          <span className="similarity">
            {Math.round(item.similarity_score * 100)}% match
          </span>
        )}
      </div>
    </div>
  );
}
```

### Similar Content Component

```javascript
// components/SimilarContent.jsx
import { useState, useEffect } from 'react';
import { getSimilarContent } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function SimilarContent({ contentType, contentId }) {
  const { token } = useAuth();
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSimilar() {
      try {
        const data = await getSimilarContent({
          contentType,
          contentId,
          limit: 6,
          token
        });
        setSimilar(data.similar_content);
      } catch (error) {
        console.error('Failed to fetch similar content:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchSimilar();
  }, [contentType, contentId, token]);

  if (loading || similar.length === 0) return null;

  return (
    <div className="similar-content">
      <h2>You might also like</h2>
      <div className="items-grid">
        {similar.map(item => (
          <RecommendationCard key={item.content_id} item={item} />
        ))}
      </div>
    </div>
  );
}
```

## Auto-Tracking Integrations

### Track Lesson Views

```javascript
// pages/lessons/[id].jsx
import { recordInteraction } from '@/lib/api';

export default function LessonPage({ lesson }) {
  const { token } = useAuth();
  const startTime = useRef(Date.now());

  useEffect(() => {
    // Record view when component mounts
    recordInteraction({
      contentType: 'lesson',
      contentId: lesson.id,
      interactionType: 'view',
      metadata: { source: 'lesson_page' },
      token
    });

    // Record duration when user leaves
    return () => {
      const duration = Math.floor((Date.now() - startTime.current) / 1000);
      recordInteraction({
        contentType: 'lesson',
        contentId: lesson.id,
        interactionType: 'view',
        durationSeconds: duration,
        metadata: { source: 'lesson_page_exit' },
        token
      });
    };
  }, [lesson.id, token]);

  return <div>{/* Lesson content */}</div>;
}
```

### Track Lesson Completion

```javascript
// When user completes a lesson
async function handleLessonComplete() {
  await recordInteraction({
    contentType: 'lesson',
    contentId: lessonId,
    interactionType: 'complete',
    durationSeconds: totalTimeSpent,
    metadata: {
      completion_percentage: 100,
      score: quizScore
    },
    token
  });
  
  // Show completion modal, etc.
}
```

### Track Like/Save Actions

```javascript
// Like button component
function LikeButton({ contentType, contentId }) {
  const [liked, setLiked] = useState(false);
  const { token } = useAuth();

  const handleLike = async () => {
    setLiked(!liked);
    
    await recordInteraction({
      contentType,
      contentId,
      interactionType: liked ? 'view' : 'like', // Remove like or add like
      metadata: { action: liked ? 'unlike' : 'like' },
      token
    });
  };

  return (
    <button onClick={handleLike}>
      {liked ? '❤️' : '🤍'} Like
    </button>
  );
}
```

## Dart/Flutter (Mobile App)

Add to `mobile/lib/services/api_service.dart`:

```dart
// Get recommendations
Future<Map<String, dynamic>> getRecommendations({
  String? recommendationType,
  int limit = 10,
}) async {
  final params = {
    if (recommendationType != null) 'recommendation_type': recommendationType,
    'limit': limit.toString(),
  };
  
  return await get('/recommendations', queryParams: params);
}

// Get similar content
Future<Map<String, dynamic>> getSimilarContent({
  required String contentType,
  required String contentId,
  int limit = 10,
}) async {
  return await get(
    '/recommendations/similar/$contentType/$contentId',
    queryParams: {'limit': limit.toString()},
  );
}

// Record interaction
Future<Map<String, dynamic>> recordInteraction({
  required String contentType,
  required String contentId,
  required String interactionType,
  int? durationSeconds,
  Map<String, dynamic>? metadata,
}) async {
  return await post('/recommendations/interaction', body: {
    'content_type': contentType,
    'content_id': contentId,
    'interaction_type': interactionType,
    if (durationSeconds != null) 'duration_seconds': durationSeconds,
    if (metadata != null) 'metadata': metadata,
  });
}
```

### Flutter Widget

```dart
class RecommendationsWidget extends StatefulWidget {
  @override
  _RecommendationsWidgetState createState() => _RecommendationsWidgetState();
}

class _RecommendationsWidgetState extends State<RecommendationsWidget> {
  Map<String, dynamic>? recommendations;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    loadRecommendations();
  }

  Future<void> loadRecommendations() async {
    try {
      final data = await ApiService().getRecommendations(limit: 5);
      setState(() {
        recommendations = data;
        loading = false;
      });
    } catch (e) {
      print('Error loading recommendations: $e');
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return CircularProgressIndicator();
    if (recommendations == null) return SizedBox.shrink();

    return Column(
      children: [
        if (recommendations!['continue_learning']?.isNotEmpty ?? false)
          RecommendationSection(
            title: 'Continue Learning',
            items: recommendations!['continue_learning'],
            icon: Icons.book,
          ),
        // Add other sections...
      ],
    );
  }
}
```

## Best Practices

### 1. Debounce View Tracking

```javascript
// Don't track every millisecond of viewing
const TRACK_INTERVAL = 30000; // 30 seconds

useEffect(() => {
  const interval = setInterval(() => {
    recordInteraction({
      contentType: 'lesson',
      contentId,
      interactionType: 'view',
      durationSeconds: 30,
      token
    });
  }, TRACK_INTERVAL);

  return () => clearInterval(interval);
}, [contentId, token]);
```

### 2. Offline Queue

```javascript
// Queue interactions when offline
class InteractionQueue {
  static queue = [];

  static async add(interaction) {
    if (navigator.onLine) {
      await recordInteraction(interaction);
    } else {
      this.queue.push(interaction);
      localStorage.setItem('interaction_queue', JSON.stringify(this.queue));
    }
  }

  static async flush() {
    while (this.queue.length > 0) {
      const interaction = this.queue.shift();
      try {
        await recordInteraction(interaction);
      } catch (error) {
        this.queue.unshift(interaction); // Put back on failure
        break;
      }
    }
    localStorage.setItem('interaction_queue', JSON.stringify(this.queue));
  }
}

// Flush when coming online
window.addEventListener('online', () => InteractionQueue.flush());
```

### 3. Error Handling

```javascript
async function safeRecordInteraction(interaction) {
  try {
    await recordInteraction(interaction);
  } catch (error) {
    // Don't let tracking errors break the app
    console.warn('Failed to record interaction:', error);
    // Optionally: queue for retry, send to error tracking, etc.
  }
}
```

## UI/UX Guidelines

### Loading States
- Show skeleton loaders while recommendations load
- Don't block the main content

### Empty States
```javascript
{recommendations?.discover_new?.length === 0 && (
  <EmptyState>
    <p>We're learning about your interests!</p>
    <p>Complete a few lessons to get personalized recommendations.</p>
  </EmptyState>
)}
```

### Feedback UI
```javascript
<div className="recommendation-actions">
  <button onClick={() => submitFeedback('helpful')}>
    👍 Helpful
  </button>
  <button onClick={() => submitFeedback('not_helpful')}>
    👎 Not for me
  </button>
</div>
```

## Testing

```javascript
// Test with Jest
describe('Recommendations', () => {
  it('should load recommendations', async () => {
    const data = await getRecommendations({ token: 'test', limit: 5 });
    expect(data).toHaveProperty('continue_learning');
    expect(data).toHaveProperty('discover_new');
  });

  it('should record interaction', async () => {
    const result = await recordInteraction({
      contentType: 'motif',
      contentId: 'test-id',
      interactionType: 'view',
      token: 'test'
    });
    expect(result.success).toBe(true);
  });
});
```

## Performance Tips

1. **Cache recommendations** for 5-10 minutes
2. **Lazy load** recommendation sections
3. **Prefetch** likely next content
4. **Batch** interaction recording when possible
5. **Defer** non-critical tracking to background

## Example App Flow

```
User opens app
  → Load recommendations in background
  → Show "Continue Learning" section first
  
User clicks on recommended lesson
  → Record view interaction
  → Navigate to lesson
  
User completes lesson
  → Record complete interaction
  → Refresh recommendations
  
User likes lesson
  → Record like interaction
  → Update similar content
```

