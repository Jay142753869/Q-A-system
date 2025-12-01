import re
import os

# 直接读取文件内容检查scripts块
file_path = os.path.join('web_interface', 'templates', 'extrapolation_result.html')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取scripts块内容
scripts_pattern = r'{%\s*block\s+scripts\s*%}(.*?){%\s*endblock\s*%}'
scripts_match = re.search(scripts_pattern, content, re.DOTALL)

if scripts_match:
    scripts_content = scripts_match.group(1)
    
    # 检查JavaScript语法结构
    print("检查JavaScript语法结构...")
    
    # 检查花括号和括号的匹配
    open_braces = scripts_content.count('{')
    close_braces = scripts_content.count('}')
    open_parens = scripts_content.count('(')
    close_parens = scripts_content.count(')')
    open_brackets = scripts_content.count('[')
    close_brackets = scripts_content.count(']')
    
    # 检查Jinja2条件标签的匹配
    if_tags = scripts_content.count('{% if')
    endif_tags = scripts_content.count('{% endif')
    
    # 输出检查结果
    print(f"花括号匹配: {{ {open_braces} vs }} {close_braces}")
    print(f"圆括号匹配: ( {open_parens} vs ) {close_parens}")
    print(f"方括号匹配: [ {open_brackets} vs ] {close_brackets}")
    print(f"Jinja2条件标签匹配: if {if_tags} vs endif {endif_tags}")
    
    # 验证语法结构是否正确
    if (open_braces == close_braces and 
        open_parens == close_parens and 
        open_brackets == close_brackets and
        if_tags == endif_tags):
        print("✅ JavaScript和Jinja2语法结构检查通过！")
        print("脚本块的花括号、括号和条件标签都正确匹配。")
    else:
        print("❌ 语法结构不匹配，请检查代码中的括号和标签。")
else:
    print("❌ 未找到scripts块")

# 输出scripts块内容的前200个字符作为参考
if 'scripts_content' in locals():
    print("\nScripts块内容预览:")
    print(scripts_content[:200] + '...')

