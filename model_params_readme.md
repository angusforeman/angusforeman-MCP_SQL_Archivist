# Model Parameter Guide for Factual Archive Access

## Recommended Settings for Grounded, Factual Responses

When working with archives and databases where accuracy is critical, use these parameter settings:

### Temperature: `0.1` (Range: 0.0-2.0)
**What it does:** Controls randomness in responses
- **0.0-0.3:** Highly focused, deterministic, factual ✅ **RECOMMENDED for archives**
- **0.4-0.7:** Balanced creativity and consistency
- **0.8-2.0:** More creative, random, less predictable

**For archives:** Keep low (0.1-0.3) to ensure consistent, fact-based responses

### Top-p (Nucleus Sampling): `0.1` (Range: 0.0-1.0)
**What it does:** Controls diversity of word choices
- **0.1-0.3:** Very focused vocabulary ✅ **RECOMMENDED for archives**
- **0.4-0.7:** Balanced word diversity
- **0.8-1.0:** Maximum vocabulary diversity

**For archives:** Keep low (0.1-0.3) to avoid creative interpretations

### Max Tokens: `1000` (Range: 1-4096+)
**What it does:** Maximum length of responses
- **500-1000:** Concise, focused answers ✅ **RECOMMENDED for archives**
- **1000-2000:** Detailed explanations
- **2000+:** Very detailed, long-form content

**For archives:** Use 500-1000 for concise, factual responses

### Presence Penalty: `0.0` (Range: 0.0-2.0)
**What it does:** Encourages or discourages new topics
- **0.0:** No penalty, natural topic flow ✅ **RECOMMENDED for archives**
- **0.5-1.0:** Moderate encouragement of new topics
- **1.5-2.0:** Strong encouragement of new topics

**For archives:** Keep at 0.0 to allow natural, focused responses about archive content

### Frequency Penalty: `0.3` (Range: 0.0-2.0)
**What it does:** Reduces repetitive phrasing
- **0.0:** No penalty on repetition
- **0.3-0.5:** Light reduction of repetition ✅ **RECOMMENDED for archives**
- **1.0-2.0:** Strong reduction of repetition

**For archives:** Use 0.3-0.5 to avoid redundant phrasing while maintaining accuracy

## Configuration in `.env` file

```env
# Optimized for factual archive queries
TEMPERATURE=0.1
TOP_P=0.1
MAX_TOKENS=1000
PRESENCE_PENALTY=0.0
FREQUENCY_PENALTY=0.3
```

## Advanced: Parameter Combinations

### Ultra-Grounded (Maximum Factual Accuracy)
```env
TEMPERATURE=0.0
TOP_P=0.05
PRESENCE_PENALTY=0.0
FREQUENCY_PENALTY=0.2
```
Use when: Absolute consistency required, like medical/legal archives

### Balanced Factual (Recommended Default)
```env
TEMPERATURE=0.1
TOP_P=0.1
PRESENCE_PENALTY=0.0
FREQUENCY_PENALTY=0.3
```
Use when: General archive access with good balance

### Slightly More Natural
```env
TEMPERATURE=0.3
TOP_P=0.3
PRESENCE_PENALTY=0.1
FREQUENCY_PENALTY=0.4
```
Use when: Want more conversational tone while staying factual

## Testing Your Settings

After changing parameters, test with queries like:
- "What information do you have about [specific topic]?"
- "Query the database for [specific data]"
- Compare responses - they should be consistent and fact-based

## Notes

- **Lower temperature + lower top-p = most grounded responses**
- Always combine with a clear system prompt emphasizing factual accuracy
- Monitor responses - if too robotic, slightly increase temperature (0.2-0.3)
- If responses vary too much, decrease temperature and top-p
