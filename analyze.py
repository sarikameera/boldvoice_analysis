import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Load the data
df = pd.read_csv('boldvoice_reviews_cleaned.csv')

# Step 1: Quantitative
# Group by version natively
version_stats = df.groupby('version').agg(
    avg_rating=('rating', 'mean'),
    review_count=('rating', 'count')
).reset_index()

# Sort versions
version_stats = version_stats.sort_values('version')

print("=== Quantitative Summary ===")
print(version_stats.to_string())

# Calculate Sentiment Velocity for newer versions vs older
# Let's say v3.6.x are "new" and v3.3.x/v3.4.x/v3.5.x are "old"
df['version_group'] = df['version'].apply(lambda x: 'Recent (3.6.x)' if str(x).startswith('3.6') else 'Older (3.3 - 3.5)')
print("\n=== Sentiment Velocity ===")
print(df.groupby('version_group')['rating'].mean())

# Visualizations
plt.figure(figsize=(14, 6))
sns.barplot(x='version', y='review_count', data=version_stats, color='skyblue')
plt.xticks(rotation=45)
plt.title('Review Volume by Version')
plt.tight_layout()
plt.savefig('review_count_by_version.png')

plt.figure(figsize=(14, 6))
sns.lineplot(x='version', y='avg_rating', data=version_stats, marker='o')
plt.xticks(rotation=45)
plt.title('Average Rating by Version (Sentiment Velocity)')
plt.ylim(1, 5.2)
plt.tight_layout()
plt.savefig('avg_rating_by_version.png')

# Step 2: Thematic Categorization
def categorize(row):
    review = row['review']
    title = row['title']
    if pd.isna(review): review = ""
    if pd.isna(title): title = ""
    text = str(review).lower() + " " + str(title).lower()
    
    # Billing/Monetization
    if any(word in text for word in ['charge', 'money', 'refund', 'subscription', 'expensive', 'fee', 'scam', 'payment', 'pay', 'cost', 'predatory', 'fraud', 'billing', 'cancel', 'trial']):
        return 'Monetization/Billing'
    # Critical Bugs
    elif any(word in text for word in ['bug', 'crash', "doesn't work", "doesn’t work", 'stuck', 'loading', 'microphone', 'airpod', 'slow', 'fail', 'error', 'log in', 'access', 'glitch']):
        return 'Critical Bugs'
    # Feature Requests
    elif any(word in text for word in ['add', 'feature', 'language', 'wish', 'hope', 'speed', 'tips', 'new materials', 'option', 'update', 'setting']):
        return 'Feature Requests'
    # UX/Content Friction
    elif any(word in text for word in ['frustrating', 'hard', 'repetitive', 'confuse', 'confusing', 'fast', 'tedious', 'skip', 'inaccurate', 'waste', 'boring', 'explanation', 'inflexible', 'terrible']):
        return 'UX/Content Friction'
    else:
        # Default to praise if high rating, otherwise just Other
        if row['rating'] >= 4:
            return 'General Praise / Success'
        else:
            return 'Other Negative / Mixed'

df['Theme'] = df.apply(categorize, axis=1)
print("\n=== Thematic Categorization ===")
print(df['Theme'].value_counts())

plt.figure(figsize=(10, 6))
theme_counts = df['Theme'].value_counts()
theme_counts.plot(kind='bar', color=sns.color_palette("muted", len(theme_counts)))
plt.title('Reviews Categorized by Theme')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('theme_distribution.png')

# Step 3: Root Cause Analysis for 1-star
one_star = df[df['rating'] == 1].copy()
def root_cause(row):
    review = row['review']
    title = row['title']
    if pd.isna(review): review = ""
    if pd.isna(title): title = ""
    text = str(review).lower() + " " + str(title).lower()
    
    if any(word in text for word in ['bug', 'crash', 'load', 'microphone', 'sync', 'work', 'recognize', 'detect', 'stuck', 'register', 'access']):
         return 'Technical (App Broke)'
    else:
         return 'Expectations-based (Price/Value/Scam)'

one_star['Root Cause'] = one_star.apply(root_cause, axis=1)
print("\n=== 1-Star Root Cause ===")
print(one_star['Root Cause'].value_counts())

plt.figure(figsize=(8, 5))
one_star['Root Cause'].value_counts().plot(kind='pie', autopct='%1.1f%%', colors=['#ff9999','#66b3ff'])
plt.title('Root Cause of 1-Star Reviews')
plt.ylabel('')
plt.tight_layout()
plt.savefig('one_star_root_cause.png')

# 2, 3, 4 Star Breakdowns
for star in [2, 3, 4]:
    star_df = df[df['rating'] == star]
    print(f"\n=== {star}-Star Themes ===")
    counts = star_df['Theme'].value_counts()
    print(counts)
    
    if len(counts) > 0:
        plt.figure(figsize=(10, 6))
        counts.plot(kind='bar', color=sns.color_palette("muted", len(counts)))
        plt.title(f'Themes for {star}-Star Reviews')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{star}_star_theme.png')

print("\nDone generating visual reports.")
