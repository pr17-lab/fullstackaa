import re
import shutil

def process_file(filepath):
    # backup first
    shutil.copyfile(filepath, filepath + '.bak')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Manual specific replacements:
    content = content.replace('min-h-screen bg-zinc-900 text-zinc-100', 'w-full text-gray-900 dark:text-zinc-100')
    
    bg_map = {
        '900': 'bg-white',
        '800': 'bg-gray-50',
        '700': 'bg-gray-100',
        '600': 'bg-gray-200',
        '900/60': 'bg-white/60',
        '900/50': 'bg-white/50',
        '800/60': 'bg-gray-50/60',
        '800/50': 'bg-gray-50/50',
        '800/40': 'bg-gray-50/40',
        '800/30': 'bg-gray-50/30',
        '800/20': 'bg-gray-50/20',
        '700/50': 'bg-gray-100/50',
    }
    
    border_map = {
        '700': 'border-gray-200',
        '600': 'border-gray-300',
        '700/50': 'border-gray-200/50',
        '700/40': 'border-gray-200/40',
        '700/30': 'border-gray-200/30',
    }
    
    text_map = {
        '100': 'text-gray-900',
        '200': 'text-gray-800',
        '300': 'text-gray-700',
        '400': 'text-gray-600',
        '500': 'text-gray-500',
        '600': 'text-gray-500',
    }
    
    hover_map = {
        'hover:bg-zinc-800': 'hover:bg-gray-100 dark:hover:bg-zinc-800',
        'hover:bg-zinc-700': 'hover:bg-gray-200 dark:hover:bg-zinc-700',
        'hover:text-zinc-300': 'hover:text-gray-700 dark:hover:text-zinc-300',
    }

    def replace_class(prefix, light_map):
        nonlocal content
        keys = sorted(light_map.keys(), key=len, reverse=True)
        for key in keys:
            light_cls = light_map[key]
            # Replace format: bg-zinc-900 -> bg-white dark:bg-zinc-900
            pat = r'(?<!dark:)(?<!-)' + prefix + r'-zinc-' + re.escape(key) + r'(?!\d)'
            rep = f"{light_cls} dark:{prefix}-zinc-{key}"
            content = re.sub(pat, rep, content)

    # First do exact hover replacements
    for k, v in hover_map.items():
        pat = r'(?<!dark:)' + re.escape(k)
        content = re.sub(pat, v, content)
        
    replace_class('bg', bg_map)
    replace_class('border', border_map)
    replace_class('text', text_map)

    # placeholder
    content = re.sub(r'(?<!dark:)placeholder:text-zinc-600', 'placeholder:text-gray-400 dark:placeholder:text-zinc-600', content)
    
    # Specific fixes
    content = content.replace('bg-indigo-900/20', 'bg-indigo-50 dark:bg-indigo-900/20')
    content = content.replace('border-indigo-500/60', 'border-indigo-300 dark:border-indigo-500/60')
    content = content.replace('bg-indigo-900/60', 'bg-indigo-50 dark:bg-indigo-900/60')
    content = content.replace('border-indigo-700/50', 'border-indigo-200 dark:border-indigo-700/50')
    content = content.replace('text-indigo-300', 'text-indigo-600 dark:text-indigo-300')
    content = content.replace('shadow-indigo-100', 'shadow-indigo-300') # give a slightly deeper shadow for light
    content = content.replace('shadow-indigo-900/40', 'shadow-indigo-200 dark:shadow-indigo-900/40')
    content = content.replace('shadow-indigo-900/30', 'shadow-indigo-200 dark:shadow-indigo-900/30')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

process_file('src/pages/InterviewPrep.tsx')
print("Done!")
