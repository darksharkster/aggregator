import feedparser
import json
import time
import os
from datetime import datetime

SITES_FILE = "sites.json"
CACHE_FILE = "cache.json"
OUTPUT_FILE = "index.html"
DEFAULT_PER_SITE = 25
DEFAULT_WATCHED = ["AI", "Linux", "Apple", "Google", "Open Source", "Security"]
WATCHED_FILE = "watched.json"

def load_sites():
    with open(SITES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_watched():
    with open(WATCHED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_all(sites):
    all_data = {}
    for name, url in sites.items():
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
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"fetched": datetime.now().isoformat(), "sites": all_data}, f)
    return all_data

def build_html(sites_data, watched):
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Tech News Aggregator</title>
<style>
body{{font-family: -apple-system, system-ui, sans-serif; background:#0f0f0f; color:#e0e0e0; margin:0; padding:10px}}
#controls{{background:#1a1a1a; padding:12px; position:sticky; top:0; z-index:10; border-bottom:1px solid #333; display:flex; gap:15px; flex-wrap:wrap; color:#e0e0e0}}
.column{{background:#1e1e1e; margin:10px 0; padding:10px; border-radius:8px; flex:1; min-width:300px; border:1px solid #2a2a2a}}
.grid{{display:flex; flex-wrap:wrap; gap:12px}}
a{{color:#58a6ff; text-decoration:none}} a:visited{{color:#bc8cff}} a:hover{{text-decoration:underline}}
.watched{{background:#665500; color:#ffeb3b; font-weight:bold; padding:0 3px; border-radius:3px}}
.hidden{{display:none !important}}
.preview{{position:fixed; background:#2a2a2a; color:#eee; padding:10px; max-width:400px; border-radius:6px; font-size:13px; display:none; z-index:100; pointer-events:none; border:1px solid #444; box-shadow:0 4px 12px rgba(0,0,0,0.5)}}
h2{{font-size:15px; border-bottom:2px solid #333; padding-bottom:5px; margin:0 0 8px 0; display:flex; justify-content:space-between; color:#f0f0f0}}
ul{{margin:0; padding:0 0 0 18px}} li{{margin:4px 0; font-size:14px}}
input, select{{background:#2a2a2a; color:#e0e0e0; border:1px solid #444; border-radius:4px; padding:3px 6px}}
</style>
</head>
<body>
<div id="controls">
<label>Headlines per site: <input id="perSite" type="number" value="{DEFAULT_PER_SITE}" min="1" max="100" style="width:60px"></label>
<label><input type="checkbox" id="togglePreview" checked> Hover preview</label>
<label><input type="checkbox" id="toggleHide" checked> Hide clicked</label>
<label>Watched words (comma): <input id="watchedInput" style="width:300px" value="{','.join(watched)}"></label>
<button onclick="apply()">Apply</button>
<div style="flex-basis:100%; font-size:13px; color:#888; margin-top:4px;">Create time: {datetime.now()}</div>
</div>
<div class="grid" id="grid"></div>
<div id="preview" class="preview"></div>
<script>
const DATA = {json.dumps(sites_data)};
let perSite = {DEFAULT_PER_SITE};
let watched = {watched};
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
                // FIXED - uses viewport coords for fixed element + keeps it on screen
                let x = e.clientX + 15;
                let y = e.clientY + 15;
                // keep inside viewport
                if (x + 420 > window.innerWidth) x = window.innerWidth - 420;
                if (y + 200 > window.innerHeight) y = e.clientY - 210;
                preview.style.left = x + 'px';
                preview.style.top = y + 'px';
                preview.innerHTML = '<b>'+item.title+'</b><br><br>'+(item.summary||'No preview');
            }});
            a.addEventListener('mouseleave', ()=>{{ preview.style.display='none'; }});
            li.appendChild(a);
            ul.appendChild(li);
        }});
        div.innerHTML = `<h2>${{site}}</h2>`;
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
    sites = load_sites()
    watched = load_watched()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            cached = json.load(f)
            data = cached["sites"]
    else:
        data = fetch_all(sites)
    build_html(data, watched)
