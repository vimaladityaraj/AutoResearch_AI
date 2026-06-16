from __future__ import annotations
import os
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv('STREAMLIT_API_BASE_URL', 'http://localhost:8002')
st.set_page_config(page_title='AutoResearch AI', page_icon='🧭', layout='wide')

st.markdown("""
<style>
.block-container {max-width: 1180px; padding-top: 2rem;}
.hero {padding: 2rem; border: 1px solid rgba(148,163,184,.18); border-radius: 24px; background: linear-gradient(135deg,#0f172a 0%,#172554 100%); box-shadow: 0 20px 60px rgba(0,0,0,.25);}
.hero h1 {font-size: 3rem; margin: 0 0 .5rem 0;}
.muted {color:#A7B3C6;}
.badge {display:inline-block; padding:.35rem .7rem; border:1px solid rgba(148,163,184,.25); border-radius:999px; margin:.25rem .35rem .25rem 0; background:rgba(15,23,42,.6); font-size:.8rem;}
.card {padding:1.1rem; border:1px solid rgba(148,163,184,.18); border-radius:18px; background:rgba(15,23,42,.72); margin:.8rem 0;}
.source {font-size:.86rem; color:#CBD5E1; border-left:3px solid #5B8CFF; padding-left:.85rem; margin:.65rem 0;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title('🧭 AutoResearch AI')
    st.caption('Autonomous competitive intelligence using local LLMs.')
    company = st.text_input('Company name', placeholder='e.g., Stripe')
    industry = st.text_input('Industry hint', placeholder='e.g., fintech / payments')
    focus = st.text_area('Research focus', placeholder='e.g., competitors, growth strategy, market risks')
    st.divider()
    st.subheader('Optional source URLs')
    urls_text = st.text_area('One URL per line', placeholder='https://company.com/about\nhttps://en.wikipedia.org/wiki/Company')
    run = st.button('Generate intelligence report', type='primary', use_container_width=True)
    st.divider()
    try:
        h = requests.get(f'{API_BASE}/health/', timeout=3).json()
        st.success(f"Backend online: {h['provider']} / {h['model']}")
    except Exception:
        st.error('Backend offline')

st.markdown("""
<div class="hero">
<h1>AutoResearch AI</h1>
<p class="muted">Generate structured market research, competitor analysis, SWOT insights, and strategic recommendations from public sources and user-provided URLs.</p>
<span class="badge">AI agent workflow</span><span class="badge">Ollama local LLM</span><span class="badge">FastAPI backend</span><span class="badge">Source summaries</span><span class="badge">Markdown export</span>
</div>
""", unsafe_allow_html=True)

if 'report' not in st.session_state:
    st.session_state.report = None

if run:
    if not company.strip():
        st.warning('Enter a company name first.')
    else:
        sources = [u.strip() for u in urls_text.splitlines() if u.strip()]
        payload = {'company_name': company.strip(), 'industry_hint': industry.strip() or None, 'focus_area': focus.strip() or None, 'sources': sources}
        with st.spinner('Research agent is collecting sources, summarizing evidence, and generating the report...'):
            r = requests.post(f'{API_BASE}/research/', json=payload, timeout=900)
            if r.ok:
                st.session_state.report = r.json()
                st.success('Report generated successfully.')
            else:
                st.error(r.text)

report = st.session_state.report
if not report:
    st.markdown('<div class="card"><h3>Start with a company name</h3><p class="muted">Add optional URLs for stronger grounding. For best results, include company About pages, Wikipedia pages, product pages, investor pages, or news articles.</p></div>', unsafe_allow_html=True)
else:
    st.header(f"Report: {report['company_name']}")
    st.subheader('Executive Summary')
    st.markdown(f"<div class='card'>{report['executive_summary']}</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.55,0.45])
    with col1:
        st.subheader('Company Overview')
        st.write(report['company_overview'])
        st.subheader('Market Signals')
        for x in report.get('market_signals',[]): st.markdown(f'- {x}')
        st.subheader('Strategic Recommendations')
        for x in report.get('strategic_recommendations',[]): st.markdown(f'- {x}')
    with col2:
        st.subheader('Competitors')
        comps = report.get('competitors', [])
        if comps: st.dataframe(pd.DataFrame(comps), use_container_width=True, hide_index=True)
        st.subheader('SWOT')
        swot = report.get('swot', {})
        for k in ['strengths','weaknesses','opportunities','threats']:
            with st.expander(k.title(), expanded=k in ['strengths','opportunities']):
                for x in swot.get(k,[]): st.markdown(f'- {x}')
    st.subheader('Sources')
    for s in report.get('sources', []):
        st.markdown(f"<div class='source'><b>{s['title']}</b><br>{s['url']}<br><span class='muted'>{s['extracted_chars']} characters extracted</span><br>{s['summary']}</div>", unsafe_allow_html=True)
    st.download_button('Download Markdown Report', data=report['markdown_report'], file_name=f"{report['company_name'].replace(' ','_')}_research_report.md", mime='text/markdown')
