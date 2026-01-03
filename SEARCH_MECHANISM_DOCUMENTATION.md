# Cirrostrats Search Mechanism - Complete Developer Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Backend Components](#backend-components)
4. [Frontend Components](#frontend-components)
5. [Data Flow](#data-flow)
6. [Key Algorithms](#key-algorithms)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [Search Types](#search-types)
10. [Performance Considerations](#performance-considerations)
11. [Known Issues & TODOs](#known-issues--todos)
12. [Refactoring Recommendations](#refactoring-recommendations)

## Overview

The Cirrostrats search mechanism is a sophisticated autocomplete system designed for aviation data (flights, airports, gates). It combines real-time fuzzy matching, popularity-based ranking, and intelligent query classification to provide accurate search suggestions.

### Key Features
- **Real-time autocomplete** with debounced input
- **Fuzzy matching** using Levenshtein distance
- **Popularity-based ranking** with sigmoid normalization
- **Multi-type search** (flights, airports, gates)
- **Recent search history** with localStorage persistence
- **Intelligent query parsing** with regex patterns
- **Search tracking** for analytics

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │    │   Backend       │      │   Database      │
│   (React)       │    │   (FastAPI)     │      │   (MongoDB)     │
├─────────────────┤    ├─────────────────┤      ├─────────────────┤
│ • SearchInput   │◄──►│ • Search Routes │ .    │ • suggestions_cache  │
│ • useSuggestions│    │ • Search Service│      │ • collection_   │
│ • useDebounce   │    │ • Query Classifier│    │   flights       │
│ • useTrackSearch│    │ • Search Interface│    │ • collection_   │
│ • Fuzzy Matching│    │ • Fuzzy Find    │      │  airports       │
└─────────────────┘    └─────────────────┘      └─────────────────┘
```

### Frontend Component Hierarchy

```
Input/
├── Index.tsx                 # Main orchestrator component
├── components/
│   └── SearchInput.tsx      # Material-UI Autocomplete wrapper
├── hooks/
│   ├── useSuggestions.ts    # Core suggestion logic
│   ├── useDebounce.ts       # Input debouncing
│   ├── useInputHandlers.ts  # Event handling
│   └── useTrackSearch.ts    # Search analytics
├── api/
│   └── searchservice.ts     # API communication
└── utils/
    └── searchUtils.ts       # Data formatting utilities
```

## Backend Components

### 1. QueryClassifier (`query_classifier.py`)

**Purpose**: Parses and categorizes search queries into types (Airports, Flights, Gates, Others)

**Key Methods**:
- `parse_query(query)`: Main parsing logic using regex patterns
- `classify_batch(queries)`: Batch processing for popularity ranking
- `normalize()`: Applies sigmoid compression to popularity scores

**Regex Patterns**:
```python
# Airport codes (ICAO format)
airport_pattern = re.compile(r"^[KkCc][A-Za-z]{3}$")

# Flight numbers (Airline code + digits)
flight_pattern = re.compile(rf"^({icao_codes})\s?(\d{{1,5}}[A-Z]?$)")
```

**Query Classification Logic**:
1. **Airports**: 4-letter codes starting with K/C (ICAO format)
2. **Flights**: Airline code + 1-5 digits (e.g., "UA1234", "DL567")
3. **Digits**: Pure numeric strings (assumed flight numbers)
4. **N-Numbers**: Aircraft registration (e.g., "N12345")
5. **Others**: Everything else

### 2. SearchInterface (`search_interface.py`)

**Purpose**: Converts backend data formats to frontend-compatible structures

**Key Methods**:
- `raw_submit_handler(search)`: Processes raw search submissions
- `query_type_frontend_conversion(doc)`: Standardizes data formats
- `search_suggestion_frontned_format(c_docs)`: Formats suggestions for frontend

**Data Standardization**:
```python
TYPE_STANDARDS = {
    'Flight': 'flight',
    'FLIGHT': 'flight', 
    'flightNumbers': 'flight',
    'Airport': 'airport',
    'AIRPORT': 'airport',
    'Terminal/Gate': 'terminal',
    'gate': 'terminal',
    'Gate': 'terminal'
}
```

### 3. Fuzzy Find (`fuzz_find.py`)

**Purpose**: Implements fuzzy string matching using fuzzywuzzy library

**Algorithm**:
1. **Short queries (≤2 chars)**: Prioritize prefix matching
2. **Longer queries**: Use fuzzy matching with 90% similarity threshold
3. **Fallback**: Parse query and attempt direct matching

**Scoring**: Uses `fuzz.partial_ratio` for autocomplete scenarios

### 4. Search Ranker (`search_ranker.py`)

**Purpose**: Real-time popularity ranking with exponential decay

**Features**:
- **Exponential decay**: Popularity decreases over time
- **Sigmoid compression**: Normalizes scores to 0-10 range
- **Recency bonus**: New searches get initial boost

**Formula**:
```python
# Decay calculation
decay_factor = math.exp(-decay_per_second * elapsed_seconds)
hits *= decay_factor

# Sigmoid compression
sigmoid = math.sqrt(1 / ((1/k) + math.exp(-(x * theta))))
```

## Frontend Components

### 1. SearchInput Component

**Technology**: Material-UI Autocomplete with custom rendering

**Key Features**:
- **FreeSolo mode**: Allows custom input
- **Highlight matching**: Uses autosuggest-highlight
- **Recent search indicators**: Purple color coding
- **Remove functionality**: X button for recent searches

**Props Flow**:
```typescript
interface SearchInputProps {
  userEmail: string;
}

// Renders Autocomplete with:
// - options: filteredSuggestions
// - onInputChange: handleInputChange
// - onChange: handleSubmit
// - renderOption: Custom highlighting
```

### 2. useSuggestions Hook

**Purpose**: Manages suggestion state and API calls

**State Management**:
```typescript
interface SuggestionsState {
  initial: FormattedSuggestion[];    // Popular suggestions (cached)
  backend: FormattedSuggestion[];    // Additional fetched suggestions
  filtered: FormattedSuggestion[];   // Final display list
  hasMore: boolean;                  // Pagination flag
}
```

**Key Logic**:
1. **Initial Load**: Fetch popular suggestions + recent searches
2. **Debounced Fetch**: Additional suggestions as user types
3. **Smart Filtering**: Recent searches prioritized, duplicates removed
4. **Dynamic Limits**: Max 5 total, recent searches take priority

### 3. useDebounce Hook

**Purpose**: Prevents excessive API calls during typing

**Implementation**:
```typescript
const useDebounce = <T>(inputValue: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(inputValue);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(inputValue);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [inputValue, delay]);
  
  return debouncedValue;
};
```

**Delay**: 240ms (optimized for human reaction time)

### 4. useInputHandlers Hook

**Purpose**: Manages all user interactions and navigation

**Key Handlers**:
- `handleSubmit`: Intelligent submission logic
- `handleInputChange`: Input state management
- `handleFocus/Blur`: UI expansion/collapse
- `saveSearchToLocalStorage`: Recent search persistence

**Submission Logic**:
1. **Dropdown Selection**: Direct navigation with structured data
2. **Raw String**: Attempt exact matching in suggestions
3. **Fallback**: API call for unknown queries
4. **Multiple Matches**: Force user selection with shake animation

## Data Flow

### 1. Initial Load Sequence

```
User Opens App
    ↓
useSuggestions Hook Initializes
    ↓
Fetch Popular Suggestions (API: /searches/suggestions/{email})
    ↓
Load Recent Searches (localStorage)
    ↓
Format & Combine Data
    ↓
Display in Autocomplete
```

### 2. User Typing Sequence

```
User Types Character
    ↓
handleInputChange Updates State
    ↓
useDebounce Delays API Call (240ms)
    ↓
fetchAdditionalSuggestions Called
    ↓
API: /searches/suggestions/{email}?query={input}
    ↓
Backend Processes Query
    ↓
Fuzzy Matching Applied
    ↓
Results Formatted & Returned
    ↓
Frontend Updates Suggestions
```

### 3. Search Submission Sequence

```
User Submits Search
    ↓
handleSubmit Determines Type
    ↓
If Dropdown Selection:
    ├── Direct Navigation to /details
    └── Save to Recent Searches
    ↓
If Raw String:
    ├── Check Exact Matches in Suggestions
    ├── If Match Found: Navigate with Matched Data
    ├── If Multiple Matches: Show Selection UI
    └── If No Match: Call Raw Query API
    ↓
trackSearch Logs Analytics
    ↓
Navigate to Details Page
```

## Key Algorithms

### 1. Query Classification Algorithm

```python
def parse_query(self, query: str) -> Dict:
    query = query.strip().upper()
    
    # Check airport pattern
    if self.airport_pattern.match(query):
        return {'category': 'Airports', 'value': query}
    
    # Check flight pattern
    elif self.flight_pattern.match(query):
        airline_code = flight_match.group(1)
        flight_number = flight_match.group(2)
        return {'category': 'Flights', 'value': {'airline_code': airline_code, 'flight_number': flight_number}}
    
    # Check if pure digits
    elif query.isdigit():
        if query[0] == '4' and len(query) == 4:
            return {'category': 'Flights', 'value': {'airline_code': 'GJS', 'flight_number': query}}
        else:
            return {'category': 'Digits', 'value': query}
    
    # Check N-number pattern
    elif self.temporary_n_number_parse_query(query=query):
        return {'category': 'Flights', 'value': query}
    
    # Default to others
    else:
        return {'category': 'Others', 'value': query}
```

### 2. Fuzzy Matching Algorithm

```python
def fuzz_find(query, data, qc, limit=5):
    # Short queries prioritize prefix matching
    if len(query) <= 2:
        prefix_matches = [item for item in data 
                         if item['fuzz_find_search_text'].startswith(query.lower())]
        
        if len(prefix_matches) >= limit:
            return prefix_matches[:limit]
        
        remaining = limit - len(prefix_matches)
        search_universe = [item for item in data if item not in prefix_matches]
    else:
        prefix_matches = []
        search_universe = data
        remaining = limit
    
    # Fuzzy matching with fuzzywuzzy
    choices = [item['fuzz_find_search_text'] for item in search_universe]
    fuzzy_matches = process.extract(
        query.lower(), 
        choices,
        limit=remaining,
        scorer=fuzz.partial_ratio
    )
    
    # Filter by similarity threshold
    fuzzy_items = [search_universe[choices.index(match)] for match, score in fuzzy_matches 
                  if score > 90]
    
    return prefix_matches + fuzzy_items
```

### 3. Popularity Ranking Algorithm

```python
def compress_sigmoid(self, x, k=1/30, theta=100, cap_height=10):
    """Sigmoid compression for popularity scores"""
    sigmoid_val = 1 / (1 + math.exp(-k*(x - theta))) * cap_height
    return sigmoid_val

def normalize(self):
    """Normalize popularity scores across all categories"""
    cc = self.classified_suggestions
    for cat, vals in cc.items():
        sa = {}
        for k, p_hit in vals.items():
            sa[k] = self.compress_sigmoid(p_hit)
        cc[cat] = sa
    return cc
```

## Database Schema

### 1. search_index Collection

**Purpose**: Cached popular suggestions for fast autocomplete

**Schema**:
```javascript
{
  "_id": ObjectId,
  "r_id": ObjectId,           // Reference to original collection
  "ph": Number,              // Popularity hits (score)
  "submits": [String],       // Array of submission timestamps
  "fid_st": String,          // Flight ID string (for flights)
  "airport_st": String,      // Airport string (for airports)
  "Terminal/Gate": String,   // Gate string (for gates)
  "fuzz_find_search_text": String  // Lowercase text for matching
}
```

### 2. collection_flights

**Purpose**: Flight data storage

**Schema**:
```javascript
{
  "_id": ObjectId,
  "flightID": String,        // e.g., "UAL1234"
  "airline_code": String,    // e.g., "UAL"
  "flight_number": String,   // e.g., "1234"
  // ... other flight data
}
```

### 3. collection_airports

**Purpose**: Airport data storage

**Schema**:
```javascript
{
  "_id": ObjectId,
  "code": String,            // Airport code (ICAO/IATA)
  "name": String,            // Airport name
  "count": Number,           // Popularity count
  // ... other airport data
}
```

### 4. test_rst Collection

**Purpose**: Raw search term tracking

**Schema**:
```javascript
{
  "_id": ObjectId,
  "rst": String,             // Raw search term
  "submits": [String]        // Array of submission timestamps
}
```

## API Endpoints

### 1. GET /searches/suggestions/{email}

**Purpose**: Fetch search suggestions

**Parameters**:
- `email`: User email for personalization
- `query`: Search query string (optional)
- `limit`: Maximum results (default: 100)

**Response**:
```json
[
  {
    "stId": "string",
    "r_id": "string",
    "display": "string",
    "type": "flight|airport|terminal",
    "ph": 5.2,
    "fuzz_find_search_text": "string"
  }
]
```

### 2. POST /searches/track

**Purpose**: Track search analytics

**Request Body**:
```json
{
  "email": "string",
  "stId": "string",
  "submitTerm": "string",
  "timestamp": "ISO string"
}
```

### 3. GET /query

**Purpose**: Handle raw search queries

**Parameters**:
- `search`: Raw search string

**Response**:
```json
{
  "label": "string",
  "display": "string", 
  "type": "string",
  "flightID": "string"
}
```

## Search Types

### 1. Flight Search

**Patterns Supported**:
- Full format: "UA1234", "DL567", "AA890"
- Digits only: "1234" (assumes UA prefix)
- N-numbers: "N12345"

**Processing**:
1. Parse airline code and flight number
2. Convert IATA to ICAO codes (UA→UAL, DL→DAL, AA→AAL)
3. Search collection_flights with regex
4. Format display with airline conversion

### 2. Airport Search

**Patterns Supported**:
- ICAO codes: "KEWR", "KORD", "CYYZ"
- IATA codes: "EWR", "ORD", "YYZ"
- Partial names: "Newark", "Chicago"

**Processing**:
1. Check code pattern first
2. Fallback to name search
3. Handle multiple matches (show selection UI)
4. Format as "CODE - Name"

### 3. Gate Search

**Patterns Supported**:
- Gate identifiers: "C101", "A23", "B45"

**Processing**:
1. Search collection_gates
2. Format as "AIRPORT - GATE Departures"
3. Use regex matching for partial matches

## Performance Considerations

### 1. Caching Strategy

**Search Index Collection**:
- Pre-loaded popular suggestions (3500+ items)
- Sorted by popularity hits
- Cached in memory for fast access

**Frontend Caching**:
- Recent searches in localStorage
- Debounced API calls (240ms)
- Smart suggestion limits (max 5)

### 2. Database Optimization

**Indexes**:
- `search_index.ph` (descending) for popularity sorting
- `collection_flights.flightID` for regex searches
- `collection_airports.code` for airport lookups

**Query Optimization**:
- Limit results with `.limit(10)`
- Use projection to reduce data transfer
- Batch operations for bulk updates

### 3. Frontend Performance

**Debouncing**:
- 240ms delay prevents excessive API calls
- Reduces server load and improves UX

**Smart Filtering**:
- Client-side filtering for recent searches
- Server-side fuzzy matching for accuracy
- Duplicate removal prevents UI clutter

## Known Issues & TODOs

### Critical Issues

1. **Data Structure Inconsistency**
   - Mixed naming conventions (Flight vs flight vs flightNumbers)
   - Inconsistent field names across collections
   - Need unified data model

2. **Search Exhaustion Handling**
   - Fallback logic is temporary and fragile
   - Doesn't handle all edge cases properly
   - Needs robust error handling

3. **Airline Code Conversion**
   - Hardcoded conversions (UA→UAL, DL→DAL)
   - Missing many airline codes
   - Should use comprehensive mapping

### Performance Issues

1. **Search Index Collection**
   - Can grow indefinitely with raw searches
   - No cleanup mechanism for old data
   - Memory usage concerns

2. **Fuzzy Matching**
   - No caching for repeated queries
   - Expensive operations on large datasets
   - Could benefit from indexing

### Feature Gaps

1. **International Support**
   - Limited to US airports (K/C prefixes)
   - Missing international airline codes
   - No multi-language support

2. **Advanced Search**
   - No date/time filtering
   - No route-based search
   - No saved searches

## Refactoring Recommendations

### 1. Data Model Unification

```typescript
// Proposed unified interface
interface SearchItem {
  id: string;
  type: 'flight' | 'airport' | 'gate';
  display: string;
  searchText: string;
  metadata: {
    airlineCode?: string;
    flightNumber?: string;
    airportCode?: string;
    gateNumber?: string;
  };
  popularity: number;
  lastUpdated: string;
}
```

### 2. Service Layer Refactoring

```python
# Proposed service architecture
class SearchService:
    def __init__(self):
        self.query_classifier = QueryClassifier()
        self.fuzzy_matcher = FuzzyMatcher()
        self.popularity_ranker = PopularityRanker()
    
    async def get_suggestions(self, query: str, user_email: str) -> List[SearchItem]:
        # Unified suggestion logic
        pass
    
    async def track_search(self, search_data: SearchData) -> None:
        # Centralized tracking
        pass
```

### 3. Frontend Hook Consolidation

```typescript
// Proposed unified hook
const useSearch = (userEmail: string) => {
  const [suggestions, setSuggestions] = useState<SearchItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<SearchItem[]>([]);
  
  // Consolidated logic for all search operations
  return {
    suggestions,
    recentSearches,
    isLoading,
    search: (query: string) => Promise<void>,
    track: (searchData: SearchData) => Promise<void>
  };
};
```

### 4. Database Schema Improvements

```javascript
// Proposed unified collection schema
{
  "_id": ObjectId,
  "type": "flight|airport|gate",
  "identifier": String,        // Primary identifier
  "display": String,          // Display text
  "searchText": String,       // Lowercase search text
  "metadata": {
    "airlineCode": String,
    "flightNumber": String,
    "airportCode": String,
    "gateNumber": String
  },
  "popularity": {
    "score": Number,
    "lastUpdated": Date,
    "decayRate": Number
  },
  "tracking": {
    "searches": [{
      "userEmail": String,
      "timestamp": Date
    }]
  }
}
```

### 5. Performance Optimizations

1. **Implement Redis Caching**
   - Cache popular suggestions
   - Cache fuzzy match results
   - Cache user-specific data

2. **Database Indexing**
   - Compound indexes for complex queries
   - Text indexes for fuzzy matching
   - TTL indexes for data cleanup

3. **Frontend Optimizations**
   - Virtual scrolling for large lists
   - Memoization for expensive operations
   - Service worker for offline support

### 6. Error Handling & Monitoring

```python
# Proposed error handling
class SearchError(Exception):
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code

class SearchService:
    async def get_suggestions(self, query: str, user_email: str):
        try:
            # Search logic
            pass
        except DatabaseError as e:
            logger.error(f"Database error: {e}")
            raise SearchError("Search temporarily unavailable", "DB_ERROR")
        except ValidationError as e:
            logger.warning(f"Invalid query: {query}")
            raise SearchError("Invalid search query", "VALIDATION_ERROR")
```

## Conclusion

The Cirrostrats search mechanism is a sophisticated system that successfully handles complex aviation data searches. While it has some technical debt and areas for improvement, the core architecture is solid and provides a good foundation for future enhancements.

Key strengths:
- Intelligent query classification
- Real-time fuzzy matching
- Popularity-based ranking
- User-friendly autocomplete experience

Areas for improvement:
- Data model consistency
- Error handling robustness
- Performance optimization
- International support

This documentation should serve as a comprehensive guide for developers looking to understand, maintain, or enhance the search functionality.


