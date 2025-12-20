
# Create check_file.py with proper Python code
import os

code = '''import os

file_path = \"essay/templates/essay/leaderboard.html\"

print(\"=== Checking leaderboard.html file ===\")
print(f\"File path: {file_path}\")
print(f\"File exists: {os.path.exists(file_path)}\")

if os.path.exists(file_path):
    with open(file_path, \"rb\") as f:
        content = f.read()
        print(f\"\\nFile size: {len(content)} bytes\")
        
        # Show first 100 bytes
        print(f\"First 100 bytes (hex): {content[:100].hex()}\")
        print(f\"First 100 bytes (as chars): {repr(content[:100])}\")
        
        # Check BOM
        print(\"\\n=== BOM Checks ===\")
        if content.startswith(b'\\xef\\xbb\\xbf'):
            print(\"❌ UTF-8 BOM detected (bad!)\")
        elif content.startswith(b'\\xff\\xfe'):
            print(\"❌ UTF-16 LE BOM detected (bad!)\")
        elif content.startswith(b'\\xfe\\xff'):
            print(\"❌ UTF-16 BE BOM detected (bad!)\")
        else:
            print(\"✅ No BOM detected (good!)\")
        
        # Check first line
        print(\"\\n=== First Line Analysis ===\")
        try:
            decoded = content.decode(\"utf-8\")
            first_line = decoded.split(\"\\n\")[0]
            print(f\"First line: {repr(first_line)}\")
            print(f\"Starts with {{% ?: {first_line.startswith('{%')}}\")
            
            if first_line.startswith('{%'):
                print(\"✅ GOOD: Starts with '{%'\")
            else:
                print(\"❌ BAD: Does NOT start with '{%'\")
                
        except Exception as e:
            print(f\"Error: {e}\")
        
else:
    print(\"\\n❌ File does not exist!\")
    print(\"Location should be: essay/templates/essay/leaderboard.html\")

print(\"\\n=== Quick Fix ===\")
print(\"1. Make sure file is in essay/templates/essay/leaderboard.html\")
print(\"2. First line must be: {% extends \\\"essay/base.html\\\" %}\")
print(\"3. No spaces or empty lines before it\")
'''

# Write to file
with open('check_file.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('✅ Created check_file.py')
