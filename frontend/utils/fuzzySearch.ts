/**
 * Smart fuzzy search utility for matching scenarios by meaning, not exact words.
 * Uses keyword extraction, synonym matching, and relevance scoring.
 */

// Common stop words to ignore in search
const STOP_WORDS = new Set([
  'i', 'me', 'my', 'myself', 'we', 'our', 'you', 'your', 'he', 'she', 'it', 'its',
  'they', 'them', 'their', 'what', 'which', 'who', 'whom', 'this', 'that', 'these',
  'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
  'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but',
  'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with',
  'about', 'against', 'between', 'through', 'during', 'before', 'after', 'above',
  'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
  'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
  'all', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
  'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
  'don', 'should', 'now', 'get', 'got', 'im', "i'm", 'dont', "don't", 'cant', "can't",
  'wont', "won't", 'would', 'could', 'gonna', 'wanna', 'like', 'really', 'also',
]);

// Synonym groups - words that mean similar things
const SYNONYM_GROUPS: string[][] = [
  ['search', 'look', 'check', 'inspect', 'go through', 'rummage', 'dig', 'examine'],
  ['phone', 'cell', 'device', 'mobile', 'smartphone'],
  ['cop', 'police', 'officer', 'law enforcement', 'detective', 'sheriff'],
  ['fire', 'fired', 'terminate', 'terminated', 'let go', 'laid off', 'sacked'],
  ['boss', 'manager', 'supervisor', 'employer'],
  ['pay', 'wage', 'salary', 'money', 'compensation', 'earnings', 'paycheck'],
  ['school', 'class', 'classroom', 'campus'],
  ['teacher', 'professor', 'instructor', 'staff'],
  ['suspend', 'suspension', 'expelled', 'expulsion', 'kicked out', 'removed'],
  ['rights', 'entitled', 'allowed', 'permitted', 'legal', 'lawful'],
  ['arrest', 'arrested', 'detained', 'custody', 'handcuffed', 'taken in'],
  ['locker', 'bag', 'backpack', 'belongings', 'stuff', 'things', 'property'],
  ['landlord', 'property manager', 'owner', 'management'],
  ['apartment', 'unit', 'flat', 'place', 'home', 'house', 'rental'],
  ['evict', 'eviction', 'kick out', 'remove', 'force out'],
  ['deposit', 'security deposit', 'money back'],
  ['break', 'rest', 'lunch', 'pause'],
  ['hours', 'schedule', 'shift', 'time'],
  ['harass', 'harassment', 'bully', 'bullying', 'hostile', 'abuse'],
  ['discriminate', 'discrimination', 'unfair', 'bias', 'prejudice', 'racist'],
  ['record', 'recording', 'film', 'filming', 'video', 'tape', 'camera'],
  ['silent', 'silence', 'quiet', 'not talk', 'shut up', 'say nothing'],
  ['lawyer', 'attorney', 'legal counsel', 'legal aid', 'public defender'],
  ['minor', 'underage', 'teen', 'teenager', 'young', 'kid', 'child', 'youth'],
  ['car', 'vehicle', 'automobile', 'ride'],
  ['fix', 'repair', 'maintenance', 'broken'],
  ['stop', 'pulled over', 'stopped', 'detain'],
  ['consent', 'permission', 'agree', 'allow', 'authorize'],
  ['refuse', 'decline', 'reject', 'say no', 'deny'],
  ['tip', 'tips', 'gratuity', 'gratuities'],
  ['contract', 'agreement', 'deal', 'arrangement'],
  ['scam', 'fraud', 'trick', 'con', 'rip off', 'ripoff'],
  ['return', 'refund', 'money back', 'exchange'],
  ['privacy', 'private', 'personal', 'confidential', 'secret'],
  ['noise', 'loud', 'noisy', 'volume', 'sound'],
  ['pet', 'dog', 'cat', 'animal', 'esa', 'service animal'],
  ['rent', 'lease', 'tenant', 'renting'],
  ['grade', 'grades', 'gpa', 'score', 'mark'],
  ['online', 'internet', 'web', 'digital', 'cyber', 'social media'],
  ['photo', 'photos', 'picture', 'image', 'pic', 'selfie'],
  ['account', 'profile', 'login'],
  ['data', 'information', 'info', 'personal data'],
];

// Build a synonym lookup map
const SYNONYM_MAP: Map<string, Set<string>> = new Map();
SYNONYM_GROUPS.forEach(group => {
  group.forEach(word => {
    const existing = SYNONYM_MAP.get(word) || new Set<string>();
    group.forEach(synonym => {
      if (synonym !== word) existing.add(synonym);
    });
    SYNONYM_MAP.set(word, existing);
  });
});

/**
 * Extract meaningful keywords from a search string
 */
function extractKeywords(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9' ]/g, ' ')
    .split(/\s+/)
    .filter(word => word.length > 1 && !STOP_WORDS.has(word));
}

/**
 * Get synonyms for a word
 */
function getSynonyms(word: string): string[] {
  const synonyms = SYNONYM_MAP.get(word);
  return synonyms ? Array.from(synonyms) : [];
}

/**
 * Score how well a scenario matches a search query.
 * Returns 0 if no match, higher scores = better match.
 */
function scoreMatch(query: string, targetQuestion: string, targetAnswer: string): number {
  const queryKeywords = extractKeywords(query);
  if (queryKeywords.length === 0) return 0;

  const targetText = `${targetQuestion} ${targetAnswer}`.toLowerCase();
  const targetWords = targetText.split(/\s+/);

  let score = 0;
  let matchedKeywords = 0;

  for (const keyword of queryKeywords) {
    // Direct word match in target
    if (targetText.includes(keyword)) {
      score += 3;
      matchedKeywords++;
      // Bonus for matching in question specifically
      if (targetQuestion.toLowerCase().includes(keyword)) {
        score += 2;
      }
      continue;
    }

    // Synonym match
    const synonyms = getSynonyms(keyword);
    let synonymMatched = false;
    for (const syn of synonyms) {
      if (targetText.includes(syn)) {
        score += 2;
        matchedKeywords++;
        synonymMatched = true;
        break;
      }
    }
    if (synonymMatched) continue;

    // Partial/stem match (e.g., "search" matches "searching", "searched")
    const stem = keyword.length > 4 ? keyword.slice(0, -2) : keyword;
    if (targetWords.some(w => w.startsWith(stem) || stem.startsWith(w.slice(0, -2)))) {
      score += 1.5;
      matchedKeywords++;
    }
  }

  // Bonus for matching most/all keywords
  const matchRatio = matchedKeywords / queryKeywords.length;
  if (matchRatio >= 0.8) score *= 1.5;
  else if (matchRatio >= 0.5) score *= 1.2;

  // Minimum threshold: at least 1 keyword must match
  return matchedKeywords > 0 ? score : 0;
}

export interface SearchResult<T> {
  item: T;
  score: number;
}

/**
 * Perform fuzzy search on a list of scenarios.
 * Returns matching items sorted by relevance score.
 */
export function fuzzySearch<T extends { question: string; short_answer: string }>(
  query: string,
  items: T[],
  maxResults: number = 20
): T[] {
  if (!query.trim()) return [];

  const results: SearchResult<T>[] = [];

  for (const item of items) {
    const score = scoreMatch(query, item.question, item.short_answer);
    if (score > 0) {
      results.push({ item, score });
    }
  }

  // Sort by score descending
  results.sort((a, b) => b.score - a.score);

  return results.slice(0, maxResults).map(r => r.item);
}

/**
 * Fuzzy search for scripts (which have 'content' field instead of 'short_answer')
 */
export function fuzzySearchScripts<T extends { question: string; content: string; category: string }>(
  query: string,
  items: T[],
  maxResults: number = 20
): T[] {
  if (!query.trim()) return [];

  const results: SearchResult<T>[] = [];

  for (const item of items) {
    const score = scoreMatch(query, item.question, item.content);
    if (score > 0) {
      results.push({ item, score });
    }
  }

  results.sort((a, b) => b.score - a.score);
  return results.slice(0, maxResults).map(r => r.item);
}
