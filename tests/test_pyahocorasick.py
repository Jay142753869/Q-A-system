# 简单测试pyahocorasick模块是否可用

try:
    import pyahocorasick as ahocorasick
    print("成功导入pyahocorasick模块")
    
    # 尝试创建自动机
    automaton = ahocorasick.Automaton()
    print("成功创建自动机对象")
    
    # 添加一些测试词
    test_words = ['test', 'example']
    for i, word in enumerate(test_words):
        automaton.add_word(word, (i, word))
    print("成功添加测试词")
    
    # 构建自动机
    automaton.make_automaton()
    print("成功构建自动机")
    
    # 测试匹配
    text = "this is a test example"
    for end_idx, (idx, matched_str) in automaton.iter(text):
        print(f"匹配到: {matched_str} 在位置: {end_idx - len(matched_str) + 1}-{end_idx}")
    
    print("模块测试成功!")
except Exception as e:
    print(f"模块测试失败: {e}")
    import traceback
    traceback.print_exc()