import os
import sys
import json
from colorama import init, Fore
import threading
from time import sleep,time
import webbrowser

Loading=True
def loading():
    global Loading
    while Loading:
        for c in '|/-\\':
            print(Fore.RESET+c,end='\r')
            sleep(0.1)
    print()
init(autoreset=True)

colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]

def load_language_map():
    with open('files.json', 'r', encoding='utf8') as f:
        lang_to_ext = json.load(f)
    ext_to_lang = {}
    for lang, exts in lang_to_ext.items():
        for ext in exts:
            ext_to_lang[ext.lower()] = lang
    return ext_to_lang

def detect_language_from_header(content):
    if any(marker in content for marker in ['#import <Foundation/', '@interface ', '@implementation ']):
        return 'Objective-C'
    elif any(kw in content for kw in [
        'std::', 'template<', 'typename ', 'class ', 
        '#include <vector>', '#include <iostream>', '#include <map>'    
    ]):
        return 'C++'
    else:
        return 'C'

def analyze_file(file_path, ext_to_lang):
    try:
        ext = os.path.splitext(file_path)[1].lstrip('.').lower()
        language = ext_to_lang.get(ext, '')
        
        with open(file_path, 'r', encoding='utf8', errors='ignore') as f:
            content = f.read()
        lines = 0
        for line in content.split('\n'):
            if line.strip():
                lines += 1
        
        if ext == 'h':
            language = detect_language_from_header(content)
        if ext == 'm':
            if any(marker in content for marker in ['@interface', '@implementation', '#import <UIKit/', '[self ', 'NS']):
                language = 'Objective-C'
            elif any(marker in content for marker in ['function ', '% ', 'end\n', 'matrix = [']):
                language = 'Matlab'
            else:
                # fallback: maybe Obj-C is more common in codebases?
                language = 'Objective-C'  # or skip?    
        return language, lines
    except Exception:
        return None, 0

def walk_files(path):
    for root, _, files in os.walk(path):
        for name in files:
            yield os.path.join(root, name)
bar_length = 100
def getLangCount(path):
    html=False
    opened=False
    if len(sys.argv) > 2 and sys.argv[2] == '-w':
        html=True
    global Loading
    threading.Thread(target=loading).start()
    ext_to_lang = load_language_map()
    files = list(walk_files(path))
    Loading=False

    langCount = {}
    for i, file in enumerate(files):
        w=i/len(files)*bar_length
        r=bar_length-w
        print(f'{['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][i%10]}|{'█'*int(w)}{' '*int(r)}|{i}/{len(files)}',end='\r',flush=True)
        lang, line_count = analyze_file(file, ext_to_lang)

        if lang and line_count > 0:
            langCount[lang] = langCount.get(lang, 0) + line_count
            draw_lang_percentages(langCount)
            if not opened:
                webbrowser.open('result.html')
                opened=True
            if html:
                draw_to_html(langCount,i/len(files),False)
                


    total_lines = sum(langCount.values())

    if html:
        draw_to_html(langCount,1,True)

    if total_lines == 0:
        print("No valid source files found.")
        return
    
import platform

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')
def draw_lang_percentages(langCount):
    total_lines = sum(langCount.values())
    clear_screen()
    # Sort by percentage
    lang_percent = [(lang, count / total_lines) for lang, count in langCount.items()]
    lang_percent.sort(key=lambda x: x[1], reverse=True)

    # Print percentages
    for i, (lang, pct) in enumerate(lang_percent):
        color = colors[i % len(colors)]
        print(f"{color}{lang}\t{pct * 100:.2f}%",flush=True)

    # Print bar
    print(Fore.RESET + "|", end="")
    
    for i, (_, pct) in enumerate(lang_percent):
        width = int(pct * bar_length)
        if width > 0:
            print(colors[i % len(colors)] + "█" * width, end="")
    print(Fore.RESET + "|")
import math
def draw_to_html(langCount,progress,done):
    total_lines = sum(langCount.values())
    lang_percent = [(lang, count / total_lines) for lang, count in langCount.items()]
    lang_percent.sort(key=lambda x: x[1], reverse=True)


    with open('htmlcolor.json', 'r', encoding='utf8') as f:\
        colors=json.load(f)['colors']
    with open('template.html', 'r', encoding='utf8') as f:
        htmlTemplate = f.read()
    with open('langName.html', 'r', encoding='utf8') as f:
        langTemplate = f.read()

    progress=math.ceil(progress*100)
    htmlTemplate=htmlTemplate.replace('{{PROGRESS}}',f'#AD5342 0%,#AD5342 {progress}%, transparent {progress}%,transparent 100%')
    LANG_INSERT='<!--LANG_INSERT-->'

    
    update='setInterval(() => {location.reload();} , 1000)'
    if not done:
        htmlTemplate=htmlTemplate.replace('{{SCRIPT_INSERT}}',update)
        htmlTemplate=htmlTemplate.replace('{{PROGRESS_START}}','')
        htmlTemplate=htmlTemplate.replace('{{PROGRESS_END}}','')
    else:
        htmlTemplate=htmlTemplate.replace('{{SCRIPT_INSERT}}','')
        htmlTemplate=htmlTemplate.replace('{{PROGRESS_START}}','<!--')
        htmlTemplate=htmlTemplate.replace('{{PROGRESS_END}}','-->')
    insertLangLeft=''
    insertLangRight=''
    left=htmlTemplate.find(LANG_INSERT)
    insertLangLeft=htmlTemplate[:left]
    right=htmlTemplate.find(LANG_INSERT)+len(LANG_INSERT)
    insertLangRight=htmlTemplate[right:]
    langs=''
    linearGradient=''
    conicGradient=''
    previousPercent=0
    previousDeg=0
    

    for i, (lang, pct) in enumerate(lang_percent):
        color = colors[i % len(colors)]
        copy=langTemplate.replace('{{COLOR}}',color).replace('{{LANG_NAME}}',f'{lang} {pct * 100:.2f}%')
        langs+=copy
        percent=math.ceil(pct * 100)-1+previousPercent
        linearGradient+=f'{color} {previousPercent}%,{color} {percent}%, white {percent}%,white {percent+1}%,'
        deg=math.ceil((percent/100)*360)-1
        conicGradient+=f'{color} {previousDeg}deg,{color} {deg}deg, white {deg}deg,white {deg+1}deg,'
        previousDeg=deg
        previousPercent=percent
    conicGradient+=f'gray {previousDeg}deg ,gray 360deg '
    linearGradient+=f'gray {previousPercent}%,gray 100% '
    result=insertLangLeft+langs+insertLangRight
    result=result.replace('{{LINEAR_PIE}}',linearGradient)
    result=result.replace('{{CONIC_PIE}}',conicGradient)
    with open('result.html', 'w', encoding='utf8') as f:
        f.write(result)
    


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    getLangCount(target)