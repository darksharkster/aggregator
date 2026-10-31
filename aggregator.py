import feedparser
import json
import time
import os
from datetime import datetime

# ---- CONFIG ----
SITES = {
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "Slashdot": "http://rss.slashdot.org/Slashdot/slashdot",
    "io9": "https://io9.gizmodo.com/rss",
    "The Register": "https://www.theregister.com/headlines.atom",
    "Reddit r/technology": "https://www.reddit.com/r/technology/.rss",
    "Gizmodo": "https://gizmodo.com/rss",
    "Engadget": "https://www.engadget.com/rss.xml",
    "Techdirt": "https://www.techdirt.com/feed/",
    "OSNews": "https://www.osnews.com/feed/",
    "Hacker News": "https://news.ycombinator.com/rss",
    "Techmeme": "https://techmeme.com/feed.xml",
    "Lifehacker": "https://lifehacker.com/rss",
    "TechCrunch": "https://techcrunch.com/feed/",
    "Neowin": "https://www.neowin.net/news/rss/",
    "Wired News": "https://www.wired.com/feed/rss",
    "Tom's Hardware": "https://www.tomshardware.com/feeds/all",
    "Mac Rumors": "https://www.macrumors.com/macrumors.xml",
    "Github Trending": "https://github.com/trending/rss",
    "New York Times Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "Phoronix": "https://www.phoronix.com/rss.php",
    "Lobsters": "https://lobste.rs/rss",
    "Linux Today": "https://www.linuxtoday.com/feed/",
    "Technology Review": "https://www.technologyreview.com/feed/",
    "Venture Beat": "https://venturebeat.com/feed/",
    "IEEE Spectrum": "https://spectrum.ieee.org/rss",
    "Science Daily Tech": "https://www.sciencedaily.com/rss/top/technology.xml",
    "9to5 Mac": "https://9to5mac.com/feed/",
    "Vox Technology": "https://www.vox.com/rss/technology/index.xml",
    "Metafilter": "https://www.metafilter.com/rss",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Product Hunt": "https://www.producthunt.com/feed",
    "Hacker Noon": "https://hackernoon.com/feed",
}

CACHE_FILE = "cache.json"
OUTPUT_FILE = "index.html"
DEFAULT_PER_SITE = 25
DEFAULT_WATCHED = ["AI", "Linux", "Apple", "Google", "Open Source", "Security"]

def fetch_all():
    all_data = {}
    for name, url in SITES.items():
        try:
            feed = feedparser.parse(url, agent="FreshNews-Aggregator/1.0")
            entries = []
            for e in feed.entries[:100]:
                entries.append({
                    "title": e.get("title","No title"),
                    "link": e.get("link","#"),
                    "summary": e.get("summary","")[:500],
                    "published": e.get("published",""),
                })
            all_data[name] = entries
            print(f"OK {name}: {len(entries)}")
        except Exception as ex:
            print(f"FAIL {name}: {ex}")
            all_data[name] = []
        time.sleep(0.3)
    with open(CACHE_FILE, "w") as f:
        json.dump({"fetched": datetime.now().isoformat(), "sites": all_data}, f)
    return all_data

def build_html(sites_data):
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Tech News Aggregator</title>
<style>
body{{font-family: -apple-system, system-ui, sans-serif; background:#f6f6f6; margin:0; padding:10px}}
#controls{{background:#fff; padding:12px; position:sticky; top:0; z-index:10; border-bottom:1px solid #ddd; display:flex; gap:15px; flex-wrap:wrap}}
.column{{background:#fff; margin:10px 0; padding:10px; border-radius:8px; flex:1; min-width:300px}}
.grid{{display:flex; flex-wrap:wrap; gap:12px}}
a{{color:#0a58ca; text-decoration:none}} a:visited{{color:#551a8b}}
.watched{{background:yellow; font-weight:bold; padding:0 2px}}
.hidden{{display:none !important}}
.preview{{position:fixed; background:#111; color:#fff; padding:10px; max-width:400px; border-radius:6px; font-size:13px; display:none; z-index:100; pointer-events:none}}
h2{{font-size:15px; border-bottom:2px solid #eee; padding-bottom:5px; margin:0 0 8px 0; display:flex; justify-content:space-between}}
ul{{margin:0; padding:0 0 0 18px}} li{{margin:4px 0; font-size:14px}}
</style>
</head>
<body>
<div id="controls">
<label>Headlines per site: <input id="perSite" type="number" value="{DEFAULT_PER_SITE}" min="1" max="100" style="width:60px"></label>
<label><input type="checkbox" id="togglePreview" checked> Hover preview</label>
<label><input type="checkbox" id="toggleHide" checked> Hide clicked</label>
<label>Watched words (comma): <input id="watchedInput" style="width:300px" value="{','.join(DEFAULT_WATCHED)}"></label>
<button onclick="apply()">Apply</button>
</div>
<div class="grid" id="grid"></div>
<div id="preview" class="preview"></div>
<script>
const DATA = {json.dumps(sites_data)};
let perSite = {DEFAULT_PER_SITE};
let watched = {json.dumps(DEFAULT_WATCHED)};

const grid = document.getElementById('grid');
const preview = document.getElementById('preview');

function render(){{
    grid.innerHTML='';
    let hideClicked = document.getElementById('toggleHide').checked;
    let clicked = JSON.parse(localStorage.getItem('clicked')||'[]');
    for(let site in DATA){{
        let div = document.createElement('div');
        div.className='column';
        let ul = document.createElement('ul');
        let entries = DATA[site].slice(0, perSite);
        entries.forEach(item=>{{
            if(hideClicked && clicked.includes(item.link)) return;
            let li = document.createElement('li');
            let a = document.createElement('a');
            a.href=item.link; a.target='_blank';
            a.dataset.summary = item.summary || '';
            let titleHtml = item.title;
            watched.forEach(w=>{{
                if(w && titleHtml.toLowerCase().includes(w.toLowerCase())){{
                    let regex = new RegExp(`(${{w}})`, 'gi');
                    titleHtml = titleHtml.replace(regex, '<span class="watched">$1</span>');
                }}
            }});
            a.innerHTML = titleHtml;
            a.addEventListener('click', ()=>{{
                clicked.push(item.link);
                localStorage.setItem('clicked', JSON.stringify(clicked));
                if(hideClicked) li.classList.add('hidden');
            }});
            a.addEventListener('mousemove', (e)=>{{
                if(!document.getElementById('togglePreview').checked) return;
                preview.style.display='block';
                preview.style.left = e.pageX+15+'px';
                preview.style.top = e.pageY+15+'px';
                preview.innerHTML = '<b>'+item.title+'</b><br><br>'+(item.summary||'No preview');
            }});
            a.addEventListener('mouseleave', ()=>{{ preview.style.display='none'; }});
            li.appendChild(a);
            ul.appendChild(li);
        }});
        div.innerHTML = `<h2>${{site}} <span style="font-weight:normal;font-size:12px">${{entries.length}}</span></h2>`;
        div.appendChild(ul);
        grid.appendChild(div);
    }}
}}

function apply(){{
    perSite = parseInt(document.getElementById('perSite').value)||25;
    watched = document.getElementById('watchedInput').value.split(',').map(s=>s.trim()).filter(Boolean);
    render();
}}

document.getElementById('perSite').addEventListener('change', apply);
render();
</script>
</body>
</html>
"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUTPUT_FILE}")

if __name__ == "__main__":
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cached = json.load(f)
            data = cached["sites"]
    else:
        data = fetch_all()
    build_html(data)
