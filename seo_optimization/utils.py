# seo_optimization/utils.py
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
import string
from collections import Counter
import openai
from django.conf import settings

# No need to download NLTK data here - we handle that in views.py
# Let any LookupError propagate up to be handled by the view functions


def calculate_readability_score(text):
    """
    Calculate the Flesch Reading Ease score
    Higher scores indicate material that is easier to read
    """
    if not text:
        return 0
    
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    
    # Filter out punctuation
    words = [word for word in words if word not in string.punctuation]
    
    if not sentences or not words:
        return 0
    
    # Count syllables (simplified approach)
    def count_syllables(word):
        word = word.lower()
        if len(word) <= 3:
            return 1
        vowels = "aeiouy"
        count = 0
        if word[0] in vowels:
            count += 1
        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count = 1
        return count
    
    syllable_count = sum(count_syllables(word) for word in words)
    
    # Calculate Flesch Reading Ease score
    word_count = len(words)
    sentence_count = len(sentences)
    
    if word_count == 0 or sentence_count == 0:
        return 0
    
    score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
    
    # Bound the score between 0 and 100
    return max(0, min(100, score))


def extract_keywords(text, num_keywords=10):
    """Extract potential keywords from text, prioritizing multi-word phrases"""
    if not text:
        return []
    
    # Tokenize and convert to lowercase
    words = word_tokenize(text.lower())
    
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 3]
    
    # Only include single words that are longer than 4 characters
    single_words = [word for word in filtered_words if len(word) > 4]
    word_freq = Counter(single_words)
    
    # Get bigrams (two-word phrases)
    bigrams = []
    for i in range(len(filtered_words) - 1):
        bigrams.append(f"{filtered_words[i]} {filtered_words[i+1]}")
    bigram_freq = Counter(bigrams)
    
    # Get trigrams (three-word phrases)
    trigrams = []
    for i in range(len(filtered_words) - 2):
        trigrams.append(f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}")
    trigram_freq = Counter(trigrams)
    
    # Create keyword dictionary with weighted scores
    all_keywords = {}
    
    # Add single words with lower weight (only if they're substantial)
    for word, count in word_freq.items():
        if len(word) > 4:  # Only include significant single words
            all_keywords[word] = count * 0.5  # Lower weight for single words
    
    # Add bigrams with higher weight
    for bigram, count in bigram_freq.items():
        if count > 1:  # Only consider bigrams that appear more than once
            all_keywords[bigram] = count * 3  # Triple weight for bigrams
    
    # Add trigrams with highest weight
    for trigram, count in trigram_freq.items():
        if count > 1:  # Only consider trigrams that appear more than once
            all_keywords[trigram] = count * 5  # Five times weight for trigrams
    
    # Sort by weight and get top keywords, favoring multi-word phrases
    keywords_with_weights = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
    
    # Filter results to prioritize multi-word phrases
    multi_word_keywords = [k for k, _ in keywords_with_weights if ' ' in k]
    single_word_keywords = [k for k, _ in keywords_with_weights if ' ' not in k]
    
    # First include all multi-word phrases (up to the limit)
    final_keywords = multi_word_keywords[:num_keywords]
    
    # If we haven't reached the limit, add single words
    remaining_slots = num_keywords - len(final_keywords)
    if remaining_slots > 0:
        final_keywords.extend(single_word_keywords[:remaining_slots])
    
    return final_keywords[:num_keywords]


def calculate_keyword_density(text, keywords):
    """Calculate the density of each keyword in the text"""
    if not text or not keywords:
        return {}
    
    # Normalize text
    text = text.lower()
    
    # Count total words
    words = word_tokenize(text)
    words = [word for word in words if word.isalnum()]
    total_words = len(words)
    
    if total_words == 0:
        return {}
    
    density = {}
    for keyword in keywords:
        # Count keyword occurrences
        # For multi-word keywords, count exact matches
        if ' ' in keyword:
            count = text.count(keyword)
        else:
            # For single words, count word boundary matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            count = len(re.findall(pattern, text))
        
        # Calculate density percentage
        if count > 0:
            density[keyword] = round((count / total_words) * 100, 2)
    
    return density


def suggest_improvements(readability_score, keyword_density):
    """Suggest improvements based on readability and keyword density"""
    suggestions = []
    
    # Readability suggestions
    if readability_score < 30:
        suggestions.append("The content is very difficult to read. Consider simplifying your language and using shorter sentences.")
    elif readability_score < 50:
        suggestions.append("The content is somewhat difficult to read. Try breaking down complex sentences and using more common words.")
    elif readability_score < 70:
        suggestions.append("The content has average readability. Consider simplifying some sections to improve accessibility.")
    
    # Keyword density suggestions
    for keyword, density in keyword_density.items():
        if density > 5:
            suggestions.append(f"The keyword '{keyword}' appears too frequently ({density}%). This may be seen as keyword stuffing.")
        elif density < 0.5:
            suggestions.append(f"The keyword '{keyword}' could be used more frequently to improve SEO.")
    
    return suggestions


def generate_meta_description(text, keywords=None, max_length=160):
    """Generate a meta description using OpenAI"""
    try:
        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Prepare the primary keywords as a comma-separated string
        keyword_text = ""
        if keywords and len(keywords) > 0:
            top_keywords = keywords[:5]  # Use top 5 keywords
            keyword_text = f"\nPrimary keywords to include: {', '.join(top_keywords)}"
        
        # Truncate the text if it's too long
        content_summary = text[:3000] if len(text) > 3000 else text
        
        # Create the prompt
        prompt = f"""Create an SEO-optimized meta description for the following content.
The meta description should:
- Be between 150-160 characters
- Include important keywords naturally
- Be compelling and encourage clicks
- Accurately summarize the content
- Not use quotes{keyword_text}

Content:
{content_summary}

Meta description:"""
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are an SEO specialist creating meta descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        meta_description = response.choices[0].message.content.strip()
        
        # Ensure it's not too long
        if len(meta_description) > max_length:
            meta_description = meta_description[:max_length-3] + "..."
            
        return meta_description
        
    except Exception as e:
        print(f"Error generating meta description: {e}")
        # Fallback to simple description if API fails
        if text:
            simple_desc = text[:max_length-3] + "..." if len(text) > max_length else text
            return simple_desc
        return ""


def calculate_seo_score(readability_score, keyword_density, has_meta_description):
    """Calculate an overall SEO score out of 100"""
    
    # Start with base score
    score = 50
    
    # Readability score (worth up to 30 points)
    readability_points = min(30, readability_score * 0.3)
    score += readability_points
    
    # Keyword density (worth up to 15 points)
    keyword_score = 0
    if keyword_density:
        # Ideal keyword density is around 1-3%
        for density in keyword_density.values():
            if 1 <= density <= 3:
                keyword_score += 3
            elif 0.5 <= density < 1 or 3 < density <= 4:
                keyword_score += 2
            elif density > 4:
                keyword_score += 1
        
        # Scale to maximum of 15 points
        keyword_score = min(15, keyword_score)
        score += keyword_score
    
    # Meta description (worth 5 points)
    if has_meta_description:
        score += 5
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))


def analyze_content_for_seo(content_text):
    """Complete SEO analysis for content text"""
    # Calculate readability
    readability_score = calculate_readability_score(content_text)
    
    # Extract and analyze keywords
    extracted_keywords = extract_keywords(content_text, num_keywords=15)
    keyword_density = calculate_keyword_density(content_text, extracted_keywords)
    
    # Generate meta description
    meta_description = generate_meta_description(content_text, extracted_keywords)
    
    # Get improvement suggestions
    improvement_suggestions = suggest_improvements(readability_score, keyword_density)
    
    # Calculate overall SEO score
    seo_score = calculate_seo_score(readability_score, keyword_density, bool(meta_description))
    
    return {
        'readability_score': readability_score,
        'suggested_keywords': extracted_keywords,
        'keyword_density': keyword_density,
        'meta_description': meta_description,
        'improvement_suggestions': improvement_suggestions,
        'seo_score': seo_score
    }
