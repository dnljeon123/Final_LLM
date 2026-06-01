"""Member 1 — Week 15 charts. Matches Week 14 style. Real numbers from member1_experiments_week15.py."""
import json, statistics, time
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from data.preprocessor import preprocess_text
from data.cache import benchmark_cache

SCALED_JSON = Path("data/samples/kaggle_dataset_v2.json")
FIGURES_DIR = Path("figures"); FIGURES_DIR.mkdir(exist_ok=True)
plt.rcParams.update({"font.size":11,"font.family":"sans-serif","axes.titlesize":13,
    "axes.titleweight":"bold","axes.labelsize":11,"axes.spines.top":False,
    "axes.spines.right":False,"figure.dpi":120,"savefig.dpi":200,"savefig.bbox":"tight"})
PHISH="#D32F2F"; LEGIT="#2E7D32"; W14="#90A4AE"; W15="#1565C0"

raw = json.load(open(SCALED_JSON, encoding="utf-8"))
recs = [preprocess_text(i["text"], label=i.get("label")) for i in raw]
texts = [i["text"] for i in raw]; labels=[i["label"] for i in raw]
phish=[r for r in recs if r.label==1]; legit=[r for r in recs if r.label==0]

# Fig 6: Scale comparison Week14 vs Week15
fig,ax=plt.subplots(figsize=(7,5))
x=np.arange(2); w=0.35
ax.bar(x-w/2,[100,100],w,label="Week 14",color=W14)
ax.bar(x+w/2,[len(phish),len(legit)],w,label="Week 15",color=W15)
ax.set_xticks(x);ax.set_xticklabels(["Phishing","Legitimate"])
ax.set_ylabel("Number of samples");ax.set_title("Figure 6: Corpus Scale-Up (200 -> 1,000 samples)")
for i,v in enumerate([100,100]):ax.text(i-w/2,v+8,str(v),ha="center",fontsize=10)
for i,v in enumerate([len(phish),len(legit)]):ax.text(i+w/2,v+8,str(v),ha="center",fontsize=10,fontweight="bold")
ax.legend();ax.set_ylim(0,600)
plt.savefig(FIGURES_DIR/"fig6_scale_comparison.png");plt.close()

# Fig 7: URL rate revision Week14 vs Week15
fig,ax=plt.subplots(figsize=(7,5))
cats=["Phishing","Legitimate"]
w14=[26,0]; pr=sum(1 for r in phish if r.urls)/len(phish)*100; lr=sum(1 for r in legit if r.urls)/len(legit)*100
w15=[pr,lr]
x=np.arange(2)
ax.bar(x-w/2,w14,w,label="Week 14 (n=200)",color=W14)
ax.bar(x+w/2,w15,w,label="Week 15 (n=1000)",color=W15)
ax.set_xticks(x);ax.set_xticklabels(cats);ax.set_ylabel("% emails containing >=1 URL")
ax.set_title("Figure 7: URL Signal Revised at Scale")
for i,v in enumerate(w14):ax.text(i-w/2,v+0.5,f"{v:.0f}%",ha="center",fontsize=10)
for i,v in enumerate(w15):ax.text(i+w/2,v+0.5,f"{v:.1f}%",ha="center",fontsize=10,fontweight="bold")
ax.legend();ax.set_ylim(0,32)
plt.savefig(FIGURES_DIR/"fig7_url_revision.png");plt.close()

# Fig 8: Cache benchmark cold vs warm
b=benchmark_cache(texts[:200],labels[:200])
fig,ax=plt.subplots(figsize=(7,5))
bars=ax.bar(["Cold (no cache)","Warm (cached)"],[b["cold_seconds"]*1000,b["warm_seconds"]*1000],
    color=[PHISH,LEGIT],width=0.55)
ax.set_ylabel("Time for 200 emails (ms)");ax.set_title(f"Figure 8: Disk Cache Speedup ({b['speedup_x']}x)")
for bar,v in zip(bars,[b["cold_seconds"]*1000,b["warm_seconds"]*1000]):
    ax.text(bar.get_x()+bar.get_width()/2,v+1,f"{v:.0f} ms",ha="center",fontsize=11,fontweight="bold")
plt.savefig(FIGURES_DIR/"fig8_cache_benchmark.png");plt.close()

# Fig 9: Length distribution revised
fig,ax=plt.subplots(figsize=(7,5))
pl=[len(r.clean_text) for r in phish]; ll=[len(r.clean_text) for r in legit]
bins=np.logspace(1,4.5,40)
ax.hist(pl,bins=bins,alpha=0.6,color=PHISH,label=f"Phishing (median {statistics.median(pl):.0f})")
ax.hist(ll,bins=bins,alpha=0.6,color=LEGIT,label=f"Legitimate (median {statistics.median(ll):.0f})")
ax.axvline(statistics.median(pl),color=PHISH,ls="--");ax.axvline(statistics.median(ll),color=LEGIT,ls="--")
ax.set_xscale("log");ax.set_xlabel("Clean body length (chars, log)");ax.set_ylabel("Count")
ax.set_title("Figure 9: Length Gap Narrows at Scale (2.8x -> 1.1x)");ax.legend()
plt.savefig(FIGURES_DIR/"fig9_length_revision.png");plt.close()

# Fig 10: Throughput / latency at scale
times=[]
for r in recs:
    s=time.perf_counter();preprocess_text(r.raw_text,label=r.label);times.append((time.perf_counter()-s)*1000)
fig,ax=plt.subplots(figsize=(7,5))
ax.boxplot([[t for t,r in zip(times,recs) if r.label==1],[t for t,r in zip(times,recs) if r.label==0]],
    labels=["Phishing","Legitimate"],patch_artist=True,
    boxprops=dict(facecolor="#BBDEFB"),medianprops=dict(color="black"),showfliers=False)
tp=len(times)/(sum(times)/1000)
ax.set_ylabel("Per-email latency (ms)")
ax.set_title(f"Figure 10: Latency at Scale ({tp:.0f} emails/sec, n=1000)")
plt.savefig(FIGURES_DIR/"fig10_throughput_scale.png");plt.close()

print("Charts written: fig6-fig10")
print(f"URL: phish {pr:.1f}% legit {lr:.1f}% | cache {b['speedup_x']}x | length P{statistics.median(pl):.0f}/L{statistics.median(ll):.0f} | tp {tp:.0f}/s")
