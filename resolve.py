
def read_file_content(file_path : str) -> str:
    with open(file_path, 'r') as file:
        return file.read()

def splitSentence(sentence : str) -> tuple[str]:
    #把子句改成元组，元组的内容为子句的文字
    tp = ()
    if sentence[0] != '(':
        # 如果句子不是以'('开始，直接将其作为单个元素的元组返回
        return (sentence,)
    sentence = sentence[1:len(sentence) - 1]
    i = 0
    cnt = 0
    while i < len(sentence):
        j = i
        while j < len(sentence):
            if sentence[j] == '(':
                cnt += 1
            if sentence[j] == ')':
                cnt -= 1
                if cnt == 0:
                    break
            j += 1
        literal = sentence[i:j + 1]
        tp += (literal,)
        i = j + 2
    return tp

def read_and_parse_file(file_content : str) -> list[tuple[str]]:
    # 将文件内容按行分割
    lines = file_content.strip().split('\n')
    #print(lines)
    # 初始化一个空的列表来保存所有的字句
    all_sentences = list()
    
    # 跳过第一行，因为它只是子句的个数
    for line in lines[1:]:
        # 移除前后的空格和换行符，并将其添加到列表中
        tp = splitSentence(line)
        #print(tp)8
        all_sentences.append(tp)
    
    return all_sentences

def isVariable(item : str) -> bool:
    #判断所给的项是不是一个变量    函数、常量（长度大于一）、变量（长度等于一）
    return len(item) == 1 and item.find('(') == -1

def parseLiteral(literal : str) -> list:
    #解析文字，返回列表，[否定（bool），谓词，参数1，参数2...]，如果有否定词，那么第一个元素为True
    res = []
    if literal[0] == '~':
        res.append(True)
        literal = literal[1:]
    else:
        res.append(False)
    end = literal.find('(')
    predicate = literal[:end]
    res.append(predicate)
    parameters = literal[end + 1:-1].split(',')
    res += parameters
    return res
 
    
def MGU(parsing_1 : list, parsing_2 : list, substitutions : dict = {}) -> bool:
    #对两个文字解析完成的列表进行MGU算法，替换后修改字典中key = 变量，value = 替换的项，返回False表示不可替换
    if parsing_1[1] != parsing_2[1] or len(parsing_1) != len(parsing_2):   #谓词不同或者参数数量不同，无法合一
        return False
    for param_1, param_2 in zip(parsing_1[2:],parsing_2[2:]):    #比较参数列表
        if param_1 == param_2:
            continue
        if '(' in param_1 and "(" in param_2:
            #处理函数的情形
            i = 0
            cnt = 0
            while param_1[i] == param_2[i]:
                if param_1[i] == '(':
                    cnt += 1
                i += 1
            param_1 = param_1[i:-cnt]           #剥离出不同的部分，这样就把有函数的部分化归为无函数的部分
            param_2 = param_2[i:-cnt]
        if not isVariable(param_1) and not isVariable(param_2):  #如果都是常量，不可替换
            return False
        if isVariable(param_1):
            if param_1 in param_2:              #执行occur检查，如果变量v出现在项t中，则不可合一
                return False
            substitutions[param_1] = param_2
        elif isVariable(param_2):
            if param_2 in param_1:
                return False                    #执行occur检查，如果变量v出现在项t中，则不可合一
            substitutions[param_2] = param_1
    return True
   
def substituteLiteral(literal : str, substitutions : dict) -> str:
    #对已知的最一般合一进行置换，返回置换后的文字
    parsing = parseLiteral(literal)
    for i in range(2, len(parsing)):
        for old, new in substitutions.items():
            parsing[i] = parsing[i].replace(old, new)
    newLiteral = ''
    if parsing[0] == True:
        newLiteral = '~'
    newLiteral += parsing[1]
    newLiteral += '('
    for i in range(2, len(parsing)):
        newLiteral += parsing[i]
        if i != len(parsing) - 1:
            newLiteral += ','
    newLiteral += ')'
    return newLiteral

def isResolvable(sentence_1 : tuple[str], sentence_2 : tuple[str]) -> tuple[int, int]:  
    #判断两个子句是否可以归结，可以则返回子句的下标（从0开始）表示第几个文字
    for i in range(len(sentence_1)):
        for j in range(len(sentence_2)):
            parsing_1 = parseLiteral(sentence_1[i])
            parsing_2 = parseLiteral(sentence_2[j])
            if (parsing_1[0] ^ parsing_2[0]) and (parsing_1[1] == parsing_2[1]):  #谓词相同，否定相反，可以归结
                substitutions = {}
                if MGU(parsing_1, parsing_2, substitutions):
                    return (i, j)
    return (-1, -1)
                
def getResolvableList(sentences : list[tuple[str]]) -> list[tuple]:
    #传入所有待归结的字句，返回可归结的列表，[字句对的编号，第几个谓词]
    resolvableList = []
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            m, n = isResolvable(sentences[i], sentences[j])
            if m != -1 and n != -1:
                resolvableList.append((i, j, m, n))
    return resolvableList

def updateResolvableList(sentences : list[tuple[str]], newSentence : tuple[str], resolvableList : list[tuple]):
    #对于一个归结出的新子句，更新可归结列表
    for i in range(len(sentences)):
        m, n = isResolvable(sentences[i], newSentence)
        if m != -1 and n != -1:
            resolvableList.append((i, len(sentences), m, n))
            
def resolveSentence(sentence_1 : tuple[str], sentence_2 : tuple[str], m : int, n : int, substitutions : dict) -> tuple[str]:
    #将可归结的两个子句进行归结，传入参数归结谓词下标，返回归结后的子句
    newSentence = set()                         #利用set进行去重
    for i in range(len(sentence_1)):
        if i == m:
            continue
        substitutedLiteral = substituteLiteral(sentence_1[i], substitutions)  #进行文字的替换
        if substitutedLiteral[0] == '~' and (substitutedLiteral[1:] in newSentence):        #自检测，检查有无矛盾句式
            return ()
        if substitutedLiteral[0] != '~':
            temp = '~' + substitutedLiteral
            if temp in newSentence:
                return ('1',)
        newSentence.add(substitutedLiteral)
    for j in range(len(sentence_2)):
        if j == n:
            continue
        substitutedLiteral = substituteLiteral(sentence_2[j], substitutions)
        if substitutedLiteral[0] == '~' and (substitutedLiteral[1:] in newSentence):
            return ()
        if substitutedLiteral[0] != '~':
            temp = '~' + substitutedLiteral
            if temp in newSentence:
                return ('1',)
        newSentence.add(substitutedLiteral)
    newSentence = list(newSentence)
    newSentence.sort()                          #排序，避免文字的顺序影响
    return tuple(newSentence)

def get_usefulList(usefulList : list, index : int, resolveRes : dict):
    if index in usefulList:
        return
    usefulList.append(index)
    get_usefulList(usefulList, resolveRes[index][0], resolveRes)
    get_usefulList(usefulList, resolveRes[index][1], resolveRes)
    

def resolve(sentences : list[tuple[str]], resolvableList : list[tuple]) :
    resolveRes = {}                             #归结结果，key = 归结子句的编号，value = 进行归结的母子句下标、文字下标、替换字典
    len0 = len(sentences)                       #原始长度
    while resolvableList != []:
        i, j, m, n = resolvableList[0]
        del resolvableList[0]
        sentence_1 = sentences[i]
        sentence_2 = sentences[j]
        parsing_1 = parseLiteral(sentence_1[m])
        parsing_2 = parseLiteral(sentence_2[n])
        substitutions = {}                      #key = 变量，value = 替换的量
        MGU(parsing_1, parsing_2, substitutions)
        newSentence = resolveSentence(sentence_1, sentence_2, m, n, substitutions)
        if newSentence in sentences or newSentence == ('1',):                    #去重，并且去掉永真式
            continue
        
        resolveRes[len(sentences)] = (i, j, m, n, substitutions)
        updateResolvableList(sentences, newSentence, resolvableList)
        sentences.append(newSentence)
        #print(sentences)
        #print(resolvableList)
        if newSentence == ():
            break
    if sentences[-1] == ():
        usefulList = [x for x in range(len0)]
        get_usefulList(usefulList, len(sentences) - 1, resolveRes)
        usefulList.sort()
        index = 1
        helpPrint = {}                      #在有用归结列表中的下标
        for i in usefulList:
            helpPrint[i] = index
            index += 1
        for i in usefulList:
            if i < len0:
                print(sentences[i])
            else:
                re = ''
                if len(sentences[resolveRes[i][0]]) != 1 and len(sentences[resolveRes[i][1]]) != 1:
                    re = str(helpPrint[resolveRes[i][0]]) + chr(resolveRes[i][2] + ord('a')) + ',' + str(helpPrint[resolveRes[i][1]]) + chr(resolveRes[i][3] + ord('a'))
                if len(sentences[resolveRes[i][0]]) == 1 and len(sentences[resolveRes[i][1]]) != 1:
                    re = str(helpPrint[resolveRes[i][0]]) + ',' + str(helpPrint[resolveRes[i][1]]) + chr(resolveRes[i][3] + ord('a'))
                if len(sentences[resolveRes[i][0]]) != 1 and len(sentences[resolveRes[i][1]]) == 1:
                    re = str(helpPrint[resolveRes[i][0]]) + chr(resolveRes[i][2] + ord('a')) + ',' + str(helpPrint[resolveRes[i][1]])
                if len(sentences[resolveRes[i][0]]) == 1 and len(sentences[resolveRes[i][1]]) == 1:
                    re = str(helpPrint[resolveRes[i][0]]) + ',' + str(helpPrint[resolveRes[i][1]])
                #print(f'R[{re}]{resolveRes[i][4]}{sentences[i]}')
                print(f'R[{re}]', end = '')
                print('{', end = '')
                #for old, new in resolveRes[i][4].items():
                    #print(f'{old}={new}', end = ',')
                temp = list(resolveRes[i][4].keys())
                for j in range(len(temp)):
                    old = temp[j]
                    new = resolveRes[i][4][old]
                    if j < len(resolveRes[i][4]) - 1:
                        print(f'{old}={new}', end = ',')
                    else:
                        print(f'{old}={new}', end = '')
                print('}', end = '')
                print(sentences[i])
                    
        print('-----------------------------------------------')
    else:
        print('不可归结')
        print('-----------------------------------------------')


def test_basicQuestion1():
    print("test for alpineclub.txt")
    file_path = r'alpineclub.txt'
    file_content = read_file_content(file_path)
    sentences = read_and_parse_file(file_content)
    resolvableList = getResolvableList(sentences)
    resolve(sentences, resolvableList)
    
def test_basicQuestion2():
    print("test for blockworld.txt")
    file_path = r'blockworld.txt'
    file_content = read_file_content(file_path)
    sentences = read_and_parse_file(file_content)
    resolvableList = getResolvableList(sentences)
    resolve(sentences, resolvableList)
    
def test_additionalQuestion1():
    print("test for additionalQuestion1.txt")
    file_path = r'additionalQuestion1.txt'
    file_content = read_file_content(file_path)
    sentences = read_and_parse_file(file_content)
    resolvableList = getResolvableList(sentences)
    resolve(sentences, resolvableList)
    
def test_additionalQuestion2():
    print("test for additionalQuestion2.txt")
    file_path = r'additionalQuestion2.txt'
    file_content = read_file_content(file_path)
    sentences = read_and_parse_file(file_content)
    resolvableList = getResolvableList(sentences)
    resolve(sentences, resolvableList)

def main():
    test_basicQuestion1()
    test_basicQuestion2()
    test_additionalQuestion1()
    test_additionalQuestion2()

if __name__ == '__main__':
    main()
