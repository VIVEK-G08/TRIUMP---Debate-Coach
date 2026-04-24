from __future__ import annotations

APP_STYLE = """
<style>
[data-testid="stAppViewContainer"] { background:#0c0c0c; }
[data-testid="stSidebar"] { background:#111; border-right:1px solid #1e1e1e; }
.stTextArea textarea { background:#141414!important; color:#e0e0e0!important; border:1px solid #2a2a2a!important; }
.stButton>button { background:#1a1a1a; color:#ccc; border:1px solid #2a2a2a; }
.stButton>button[kind="primary"] { background:#e0e0e0!important; color:#0c0c0c!important; border:none!important; font-weight:600; }
.mcard { background:#141414; border:1px solid #1e1e1e; border-radius:8px; padding:14px 18px; text-align:center; }
.mcard-label { font-size:10px; color:#555; text-transform:uppercase; letter-spacing:.07em; margin-bottom:4px; }
.mcard-val { font-size:26px; font-weight:600; color:#e0e0e0; }
.mcard-sub { font-size:11px; color:#444; margin-top:3px; }
.pill { display:inline-block; font-size:11px; padding:2px 10px; border-radius:20px;
	background:#161616; color:#666; border:1px solid #222; margin:2px; }
.log-card { background:#111; border:1px solid #1e1e1e; border-radius:6px; padding:10px 12px; margin-bottom:8px; }
.v-supported { color:#4caf50; font-weight:600; }
.v-contested { color:#ff9800; font-weight:600; }
.v-unsupported { color:#f44336; font-weight:600; }
.v-found { color:#4caf50; font-weight:600; }
.v-not-found { color:#666; font-weight:600; }
.formula-box { background:#0f0f0f; border:1px solid #1e1e1e; border-radius:6px;
	       padding:12px 16px; font-family:monospace; font-size:12px; color:#666; margin:8px 0; }
.sticky-col { position:sticky; top:90px; max-height:calc(100vh - 100px); overflow-y:auto; padding-right:4px; }
</style>
"""
