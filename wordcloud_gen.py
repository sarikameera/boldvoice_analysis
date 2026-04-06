import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

df = pd.read_csv('boldvoice_reviews_cleaned.csv')

def is_feature_request(row):
    text = str(row['review']).lower() + " " + str(row['title']).lower()
    return any(word in text for word in ['add', 'feature', 'language', 'wish', 'hope', 'speed', 'tips', 'new materials', 'option', 'update', 'setting'])

df['is_req'] = df.apply(is_feature_request, axis=1)
feature_reviews = df[df['is_req']]['review'].dropna().tolist()

text = " ".join(feature_reviews)

# Generate word cloud
wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='viridis', max_words=50).generate(text)

plt.figure(figsize=(10, 5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Feature Requests Word Cloud')
plt.tight_layout()
plt.savefig('feature_wordcloud.png')
print("Word cloud generated!")
