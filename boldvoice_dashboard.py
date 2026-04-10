import streamlit as st
import pandas as pd
import plotly.express as px
from textblob import TextBlob
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="BoldVoice Product Analytics Dashboard", page_icon="📈", layout="wide")

# Custom CSS for styling
st.markdown("""
<style>
    /* Sleek container styling */
    .main .block-container {
        padding-top: 2rem;
    }
    /* Larger Tab Text */
    button[data-baseweb="tab"] {
        font-size: 20px !important;
        margin-right: 40px !important;
    }
    div[data-baseweb="tab-list"] button p {
        font-size: 20px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("boldvoice_all_reviews.csv")
    df['date'] = pd.to_datetime(df['date'])
    df['review'] = df['review'].fillna('')
    df['title'] = df['title'].fillna('')
    df['text'] = df['title'] + " " + df['review']
    df['text_lower'] = df['text'].str.lower()
    return df

try:
    st.image("boldvoice.webp", width=80)
except:
    pass

st.title("BoldVoice App Review Dashboard")

with st.spinner("Analyzing review data..."):
    df = load_data()

    # Thematic Categorization
    def categorize_theme(text):
        if any(word in text for word in ['charge', 'money', 'refund', 'subscription', 'expensive', 'fee', 'scam', 'payment', 'pay', 'trial', 'cancel']):
            return 'Monetization & Pricing'
        elif any(word in text for word in ['bug', 'crash', "doesn't work", 'stuck', 'loading', 'microphone', 'airpod', 'slow', 'error', 'freeze']):
            return 'UX Friction & Bugs'
        elif any(word in text for word in ['add', 'feature', 'language', 'wish', 'hope', 'speed', 'tips', 'new materials', 'missing']):
            return 'Feature Requests'
        elif any(word in text for word in ['improve', 'learn', 'practice', 'pronounce', 'accent', 'helpful', 'confidence', 'speak', 'english']):
            return 'Pedagogical Value'
        elif any(word in text for word in ['great', 'love', 'amazing', 'awesome', 'good', 'best', 'perfect', 'fantastic', 'excellent', 'nice']):
            return 'Generic Praise'
        else:
            return 'Uncategorized/Short'

    df['Theme'] = df['text_lower'].apply(categorize_theme)
    
    # Sentiment (TextBlob)
    df['Sentiment_Score'] = df['text_lower'].apply(lambda x: TextBlob(x).sentiment.polarity)
    
    # Personas
    def tag_persona(text):
        if any(word in text for word in ['professional', 'work', 'job', 'career', 'interview', 'meeting', 'colleague', 'business', 'office', 'presentation', 'coworker', 'boss', 'client']):
            return 'Professional'
        elif any(word in text for word in ['student', 'school', 'class', 'exam', 'test', 'university', 'college', 'professor', 'teacher', 'studying', 'grade']):
            return 'Student'
        elif any(word in text for word in ['beginner', 'start', 'new to english', 'basics', 'learning english', 'just started', 'easy']):
            return 'Beginner'
        elif any(word in text for word in ['non-native', 'accent', 'esl', 'foreigner', 'pronunciation', 'speak like native', 'native speaker', 'foreign', 'immigrant', 'american accent', 'syllable', 'vowel']):
            return 'Accent Improver'
        else:
            return 'General User'
            
    df['Persona'] = df['text_lower'].apply(tag_persona)
    
    # Pain Points (1 and 2 stars only)
    def identify_pain_point(row):
        if row['rating'] > 2:
            return 'N/A'
        text = row['text_lower']
        
        # Micro/Audio
        if any(word in text for word in ['microphone', 'hear', 'detect', 'record', 'audio', 'pick up']):
            if any(word in text for word in ['airpod', 'bluetooth', 'sync', 'disconnect']):
                return 'Bluetooth/AirPods Syncing'
            return 'Microphone Detection Failure'
        
        # Crashing / Bugs
        elif any(word in text for word in ['crash', 'freeze', 'blank', 'stuck', 'load', 'open', 'close']):
            return 'App Crashing / Freezing'
            
        # Account / Login
        elif any(word in text for word in ['login', 'log in', 'sign in', 'account', 'password', 'register']):
            return 'Account Access / Login Bugs'
            
        # Billing
        elif any(word in text for word in ['cancel', 'refund', 'scam', 'unsub', 'predatory', 'fraud', 'robbed']):
            return 'Subscription Cancellation Friction'
        elif any(word in text for word in ['expensive', 'charge', 'money', 'price', 'cost', 'paywall', 'trial']):
            return 'Price Objection / Paywall'
            
        # UX / Pedagogy
        elif any(word in text for word in ['confusing', 'hard', 'repetitive', 'fake', 'useless', 'terrible', 'fast', 'accuracy', 'inaccurate']):
            return 'Pedagogical/Feedback Frustration'
            
        else:
            return 'Other Vague Negative'
            
    df['Pain Point'] = df.apply(identify_pain_point, axis=1)

# Executive Summary
st.markdown("### Executive Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Reviews Analyzed", len(df))
col2.metric("Data Source", df['source'].iloc[0] if 'source' in df.columns else "App Store")
col3.metric("Average Rating", round(df['rating'].mean(), 2))
col4.metric("Avg Sentiment Score", round(df['Sentiment_Score'].mean(), 2))

st.markdown("""
- **Sentiment & Ratings**: Overall user reception is largely positive, with distinct feedback cohorts.
- **Pain Points**: For lower-rated reviews, users predominantly site *Audio/Microphone Issues* and *Pricing*.
- **Personas Engine**: Professionals and Accent Improvers represent the largest identifiable user demographics in the reviews.
""")

st.divider()

# Create Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Thematic Analysis", "User Personas", "Pain Points", "Mixed Feedback (3-4 Stars)", "Feature Suggestions"])

with tab1:
    st.subheader("What are users talking about?")
    col_a, col_b = st.columns(2)
    
    with col_a:
        theme_counts = df['Theme'].value_counts().reset_index()
        theme_counts.columns = ['Theme', 'Count']
        fig_theme = px.pie(theme_counts, names='Theme', values='Count', hole=0.4, title='Overall Review Themes', color_discrete_sequence=px.colors.qualitative.Vivid)
        st.plotly_chart(fig_theme, use_container_width=True)
        
    with col_b:
        theme_stars = df.groupby(['rating', 'Theme']).size().reset_index(name='Count')
        fig_theme_star = px.bar(theme_stars, x='rating', y='Count', color='Theme', title='What Drives Each Rating? (100% Normalized)', color_discrete_sequence=px.colors.qualitative.Vivid)
        fig_theme_star.update_layout(barmode='stack', barnorm='percent', yaxis_title='Percentage of Reviews within Tier (%)')
        fig_theme_star.update_xaxes(type='category', categoryorder='category ascending', title='Star Rating')
        st.plotly_chart(fig_theme_star, use_container_width=True)
        
    st.markdown("### Sentiment Velocity")
    # Group by month (or week for 500 reviews)
    df['Week'] = df['date'].dt.to_period('W').dt.start_time
    trend_df = df.groupby('Week').agg({'rating': 'mean', 'review_id': 'count'}).reset_index()
    fig_velocity = px.line(trend_df, x='Week', y='rating', title='Average Rating Over Time', markers=True)
    st.plotly_chart(fig_velocity, use_container_width=True)

with tab2:
    st.subheader("Who is using BoldVoice?")
    
    col_c, col_d = st.columns(2)
    
    persona_filtered = df[df['Persona'] != 'General User']
    
    with col_c:
        persona_counts = persona_filtered['Persona'].value_counts().reset_index()
        persona_counts.columns = ['Persona', 'Reviews']
        fig_persona = px.bar(persona_counts, x='Persona', y='Reviews', title='Identified User Personas', text='Reviews', color='Persona', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_persona.update_layout(xaxis_title="", showlegend=False)
        st.plotly_chart(fig_persona, use_container_width=True)
        
    with col_d:
        persona_stars = persona_filtered.groupby(['Persona', 'rating']).size().reset_index(name='Count')
        fig_p_stars = px.bar(persona_stars, x='rating', y='Count', color='Persona', title='Star Ratings by Persona', facet_col='Persona', facet_col_wrap=2, height=700, color_discrete_sequence=px.colors.qualitative.Pastel, facet_col_spacing=0.15, facet_row_spacing=0.15)
        fig_p_stars.update_xaxes(type='category', categoryorder='category ascending', title_text='')
        fig_p_stars.update_yaxes(matches=None, showticklabels=True)
        fig_p_stars.update_layout(showlegend=False)
        fig_p_stars.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig_p_stars, use_container_width=True)

    st.markdown("### What Each Persona Likes & Dislikes")
    c_e, c_f = st.columns(2)
    
    with c_e:
        likes_df = persona_filtered[persona_filtered['rating'] >= 4]
        likes_counts = likes_df.groupby(['Persona', 'Theme']).size().reset_index(name='Count')
        fig_likes = px.bar(likes_counts, x='Count', y='Persona', color='Theme', orientation='h', title='Top Praises (4-5 Star Reviews)', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_likes.update_layout(yaxis_title='', legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_likes, use_container_width=True)
        
    with c_f:
        dislikes_df = persona_filtered[persona_filtered['rating'] <= 3]
        dislikes_counts = dislikes_df.groupby(['Persona', 'Theme']).size().reset_index(name='Count')
        fig_dislikes = px.bar(dislikes_counts, x='Count', y='Persona', color='Theme', orientation='h', title='Top Gripes (1-3 Star Reviews)', color_discrete_sequence=px.colors.qualitative.Vivid)
        fig_dislikes.update_layout(yaxis_title='', legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_dislikes, use_container_width=True)
        
with tab3:
    st.subheader("What drives users to churn? (1 & 2 Star Reviews)")
    
    pain_df = df[df['Pain Point'] != 'N/A']
    if len(pain_df) > 0:
        st.markdown("**Root Cause Deep Dive**: Instead of generic negative themes, this isolates critical 1 and 2-star reviews into highly specific actionable broken workflows—ranging from exact UI bugs to precise billing disputes.")
        c1, c2 = st.columns([1, 1])
        with c1:
            pain_counts = pain_df['Pain Point'].value_counts().reset_index()
            pain_counts.columns = ['Pain Point', 'Count']
            pain_counts = pain_counts.sort_values('Count', ascending=True)
            fig_pain = px.bar(pain_counts, x='Count', y='Pain Point', orientation='h', title='Root Causes of Critical Reviews', color='Pain Point', color_discrete_sequence=px.colors.sequential.RdBu)
            fig_pain.update_layout(showlegend=False)
            st.plotly_chart(fig_pain, use_container_width=True)
            
        with c2:
            st.markdown("##### Recent Critical Reviews")
            pain_options = ['All Critical Reviews'] + list(pain_counts['Pain Point'])
            selected_pain = st.selectbox("Select an issue to filter reviews:", pain_options)
            
            if selected_pain != 'All Critical Reviews':
                filtered_pdf = pain_df[pain_df['Pain Point'] == selected_pain]
            else:
                filtered_pdf = pain_df
                
            st.write(f"**{len(filtered_pdf)} reviews found** matching this criteria.")
            st.dataframe(filtered_pdf.sort_values('date', ascending=False)[['date', 'rating', 'version', 'Pain Point', 'title', 'review']].head(20), use_container_width=True)
    else:
        st.info("No 1 or 2 star reviews found in this dataset!")

with tab4:
    st.subheader("What holds back a full 5-star rating? (3 & 4 Star Reviews)")
    
    mixed_df = df[df['rating'].isin([3, 4])].copy()
    
    if len(mixed_df) > 0:
        st.markdown("**Deep Insights Overview**: Users giving 3 or 4 stars generally like the app but withhold a perfect score due to mild friction. Below are the highly specific problems they run into based on deep keyword extraction.")
        
        def extract_deep_insight(text):
            if any(word in text for word in ['fast', 'speed', 'pace', 'pacing', 'quick']):
                return 'Pacing Too Fast'
            elif any(word in text for word in ['repetitive', 'boring', 'tedious', 'variety', 'same']):
                return 'Repetitive Content'
            elif any(word in text for word in ['detect', 'microphone', 'recognize', 'understand', 'pick up', 'inaccurate']):
                return 'Speech Detection Inaccuracy'
            elif any(word in text for word in ['expensive', 'trial', 'subscription', 'price', 'cost']):
                return 'Price / Trial Friction'
            elif any(word in text for word in ['more', 'add', 'wish', 'missing', 'level', 'language']):
                return 'Missing Specific Content'
            else:
                return 'General Minor Gripes'
                
        mixed_df['Specific Insight'] = mixed_df['text_lower'].apply(extract_deep_insight)
        
        c3, c4 = st.columns([1, 1])
        with c3:
            mixed_counts = mixed_df['Specific Insight'].value_counts().reset_index()
            mixed_counts.columns = ['Specific Problem', 'Count']
            mixed_counts = mixed_counts.sort_values('Count', ascending=True)
            fig_mixed = px.bar(mixed_counts, x='Count', y='Specific Problem', orientation='h', title='Deep Insights on Mixed Reviews', color='Specific Problem', color_discrete_sequence=px.colors.sequential.Aggrnyl)
            fig_mixed.update_layout(showlegend=False)
            st.plotly_chart(fig_mixed, use_container_width=True)
            
        with c4:
            st.markdown("##### Recent Mixed Reviews")
            mixed_options = ['All Mixed Reviews'] + list(mixed_counts['Specific Problem'])
            selected_mixed = st.selectbox("Select an issue to filter reviews:", mixed_options)
            
            if selected_mixed != 'All Mixed Reviews':
                filtered_mdf = mixed_df[mixed_df['Specific Insight'] == selected_mixed]
            else:
                filtered_mdf = mixed_df
                
            st.write(f"**{len(filtered_mdf)} reviews found** matching this criteria.")
            st.dataframe(filtered_mdf.sort_values('date', ascending=False)[['date', 'rating', 'version', 'Specific Insight', 'review']].head(20), use_container_width=True)
            
    else:
        st.info("No 3 or 4 star reviews found in this dataset!")

with tab5:
    st.subheader("Feature Suggestions & Wishlist")
    
    # Filter for reviews that ask for features
    feature_df = df[df['Theme'] == 'Feature Requests'].copy()
    
    if len(feature_df) > 0:
        st.markdown("**Roadmap Deep Dive**: What specifically are users asking for to improve the app? We've extracted exactly what features are blocking deeper engagement.")
        
        def analyze_feature_request(text):
            if any(word in text for word in ['language', 'spanish', 'french', 'portuguese', 'native', 'tongue', 'support']):
                return 'New Native Languages'
            elif any(word in text for word in ['level', 'advanced', 'more content', 'materials', 'lesson', 'longer']):
                return 'More Levels / Content'
            elif any(word in text for word in ['speed', 'slow', 'fast', 'pace', 'control']):
                return 'Playback Speed Controls'
            elif any(word in text for word in ['meaning', 'translate', 'translation', 'dictionary', 'define', 'definition']):
                return 'Dictionary / Translation'
            elif any(word in text for word in ['conversation', 'chat', 'live', 'talk to', 'bot', 'real person']):
                return 'Live Conversation / Chatbot'
            else:
                return 'General Feature/Other'

        feature_df['Specific Feature'] = feature_df['text_lower'].apply(analyze_feature_request)
        
        c5, c6 = st.columns([1, 1])
        
        with c5:
            feature_counts = feature_df['Specific Feature'].value_counts().reset_index()
            feature_counts.columns = ['Requested Feature', 'Count']
            feature_counts = feature_counts.sort_values('Count', ascending=True)
            fig_feat = px.bar(feature_counts, x='Count', y='Requested Feature', orientation='h', title='Top Requested Features', color='Requested Feature', color_discrete_sequence=px.colors.sequential.Plasma)
            fig_feat.update_layout(showlegend=False)
            st.plotly_chart(fig_feat, use_container_width=True)
            
        with c6:
            st.markdown("##### Recent Feature Requests")
            feature_options = ['All Feature Requests'] + list(feature_counts['Requested Feature'][::-1]) # Reverse to show largest first
            selected_feat = st.selectbox("Select a feature to filter reviews:", feature_options)
            
            if selected_feat != 'All Feature Requests':
                filtered_feat_df = feature_df[feature_df['Specific Feature'] == selected_feat]
            else:
                filtered_feat_df = feature_df
                
            st.write(f"**{len(filtered_feat_df)} reviews found** matching this criteria.")
            st.dataframe(filtered_feat_df.sort_values('date', ascending=False)[['date', 'rating', 'version', 'Specific Feature', 'title', 'review']].head(20), use_container_width=True)
            
    else:
        st.info("No feature requests identified based on our keyword mapping.")
