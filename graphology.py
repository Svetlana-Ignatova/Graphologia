import cv2
import numpy as np


# эти функции пригодятся нам в дальнейшем

# функция для вычисления горизонтальных проекций
def horizontalProjection(img):
    # Возвращает список суммы пикселей в каждой строке
    (h, w) = img.shape[:2]
    sumRows = []
    for j in range(h):
        row = img[j:j + 1, 0:w]  # y1:y2, x1:x2
        sumRows.append(np.sum(row))
    return sumRows

# функция для вычисления вертикальных проекций
def verticalProjection(img):
    # Возвращает список суммы пикселей в каждом столбце
    (h, w) = img.shape[:2]
    sumCols = []
    for j in range(w):
        col = img[0:h, j:j + 1]  # y1:y2, x1:x2
        sumCols.append(np.sum(col))
    return sumCols


angle_size = 0
kolvo_strok = 0
angle_sum = 0
mezh_str_intrv = 0
verh_pole = 0

# импорт изображения
image = cv2.imread('img.jpg')  # название изображения
cv2.imshow('orig', image)
cv2.waitKey(0)
# меняем размер изобржения на стандартный
image = cv2.resize(image, (1240, 886), interpolation=cv2.INTER_AREA)
#cv2.imshow('change size', image)
image = cv2.medianBlur(image,5)

# перевод в оттенки серого
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#cv2.imshow('shades gray', gray)
#cv2.waitKey(0)

# копия изображения
gray1 = gray

# размытие изображение
gray = cv2.medianBlur(gray, 5)
#cv2.imshow('blur', gray)
#cv2.waitKey(0)

# бинаризация (перевод в чёрный и белый) для размытого изображения
ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
#cv2.imshow('binar', thresh)
#cv2.waitKey(0)

#бинаризация для чёткого изображения
ret1, thresh1 = cv2.threshold(gray1, 127, 255, cv2.THRESH_BINARY_INV)

# расширение символов
kernel = np.ones((1, 100), np.uint8)
img_dilation = cv2.dilate(thresh, kernel, iterations=1)
#cv2.imshow('dilated', img_dilation)
#cv2.waitKey(0)

# поиск контуров
ctrs, hier = cv2.findContours(img_dilation.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for i, ctr in enumerate(ctrs):
    # создаём рамки-границы
    x, y, w, h = cv2.boundingRect(ctr)

    # вывод строк и подсчёт их количества
    if h > w or h < 20:
        continue
    roi = image[y:y + h, x:x + w]
    kolvo_strok = kolvo_strok + 1
    '''
    #вывод на экран сегментов
    cv2.imshow('segment no:'+str(i),roi)
    cv2.rectangle(image,(x,y),( x + w, y + h ),(90,0,255),2)
    cv2.waitKey()
    '''
    # ищем прямоугольники, описывающие контуры строк и изображаем их
    rect = cv2.minAreaRect(ctr)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    cv2.drawContours(image, [box], 0, (0, 0, 255), 2)
    angle = rect[2]
    if angle < -45.0:
        angle += 90.0;
    angle_sum += angle

# ищем средние значение угла наклона
angle_size = angle_sum / kolvo_strok
print("Величина угла наклона строки: ", angle_size)

#наглядное изображение контуров строк
cv2.imshow('image with frames', image)
cv2.waitKey(0)

# извлекаем горизонтальную проекцию
hpList = horizontalProjection(thresh1)

# ищем размеры верхнего поля
VerhPoleCount = 0
for sum in hpList:
    # сумма может быть от нуля до 255, чтобы мы могли считать строку пустой
    if (sum <= 255):
        VerhPoleCount += 1
    else:
        break

# print("Верхнее поле в строках: ", VerhPoleCount)

# исследуем горизонтальную проекцию
lineTop = 0
lineBottom = 0
spaceTop = 0
spaceBottom = 0
indexCount = 0
setLineTop = True
setSpaceTop = True
includeNextSpace = True
space_zero = []  # количество пробелов между строками
lines = []  # 2D-список, хранящий вертикальный начальный индекс и конечный индекс каждого контура

for i, sum in enumerate(hpList):
    # если ноль, то значит пустая строка
    if (sum == 0):
        if (setSpaceTop):
            spaceTop = indexCount
            setSpaceTop = False  # устанавливается один раз для каждого начала пробела(между строками)
        indexCount += 1
        spaceBottom = indexCount
        if (i < len(hpList) - 1):  # предотвращение ошибки выхода за границы массива
            if (hpList[i + 1] == 0):  # если следующая горизонтальная проекция равна 0, продолжаем считать, что это пробел
                continue
        # мы используем это условие, если предыдущий контур очень тонкий и, возможно, не является строкой
        if (includeNextSpace):
            space_zero.append(spaceBottom - spaceTop)
        else:
            if (len(space_zero) == 0):
                previous = 0
            else:
                previous = space_zero.pop()
            space_zero.append(previous + spaceBottom - lineTop)
        setSpaceTop = True  # при следующей встрече 0, это будет новый пробел, поэтому устанавливаем новый SetSpace

    # если больше 0, то контур
    if (sum > 0):
        if (setLineTop):
            lineTop = indexCount
            setLineTop = False  # устанавливается один раз для каждого начала пробела(между строками)
        indexCount += 1
        lineBottom = indexCount
        if (i < len(hpList) - 1):
            if (hpList[i + 1] > 0):
                continue

            if (lineBottom - lineTop < 20):
                includeNextSpace = False
                setLineTop = True
                continue
        includeNextSpace = True

        lines.append([lineTop, lineBottom])
        setLineTop = True

ANCHOR_POINT = 6000
# здесь мы исследуем отдельные штрихи в уже сформированных группах
fineLines = []  # начальный  и конечный индексы каждой отдельной строки
for i, line in enumerate(lines):

    anchor = line[0]  # 'anchor' будет определять горизонтальные индексы, где горизонтальная проекция> ANCHOR_POINT для подъема или <ANCHOR_POINT для спуска
    anchorPoints = []  # список, в котором будем хранить anchor
    upHill = True  # это означает, что мы ожидаем найти начало отдельной строки (по вертикали), поднимаясь по гистограмме
    downHill = False  # это означает, что мы ожидаем найти конец отдельной строки (по вертикали), спускаясь вниз по гистограмме
    segment = hpList[line[0]:line[1]]  # здесь помещаем интересующую область горизонтальной проекции каждого контура

    for j, sum in enumerate(segment):
        if (upHill):
            if (sum < ANCHOR_POINT):
                anchor += 1
                continue
            anchorPoints.append(anchor)
            upHill = False
            downHill = True
        if (downHill):
            if (sum > ANCHOR_POINT):
                anchor += 1
                continue
            anchorPoints.append(anchor)
            downHill = False
            upHill = True

    #print(anchorPoints)

    # условие для игнорирования контура
    if (len(anchorPoints) < 2):
        continue
    # контур - отдельная линия
    if (len(anchorPoints) <= 3):
        fineLines.append(line)
        continue
    # len (anchorPoints)> 3 означает контур, состоящий из нескольких линий
    lineTop = line[0]
    for x in range(1, len(anchorPoints) - 1, 2):
        # 'lineMid' - горизонтальный индекс, по которому будет выполняться сегментация
        lineMid = (anchorPoints[x] + anchorPoints[x + 1]) / 2
        lineBottom = lineMid
        # строка с высотой пикселей <20 считается дефектом, поэтому мы ее просто игнорируем
        if (lineBottom - lineTop < 20):
            continue
        fineLines.append([lineTop, lineBottom])
        lineTop = lineBottom
    if (line[1] - lineTop < 20):
        continue
    fineLines.append([lineTop, line[1]])

# Находим РАЗМЕР БУКВ и МЕЖСТРОЧНЫЙ ИНТЕРВАЛ!

MIDZONE_THRESHOLD = 15000
space_nonzero_row_count = 0
midzone_row_count = 0
lines_having_midzone_count = 0
flag = False
for i, line in enumerate(fineLines):
    a = int(line[0])
    b = int(line[1])
    segment = hpList[a.__index__():b.__index__()]
    for j, sum in enumerate(segment):
        if (sum < MIDZONE_THRESHOLD):
            space_nonzero_row_count += 1
        else:
            midzone_row_count += 1
            flag = True

    if (flag):
        lines_having_midzone_count += 1
        flag = False

# предотвращение ошибок
if (lines_having_midzone_count == 0): lines_having_midzone_count = 1

total_space_row_count = space_nonzero_row_count + np.sum(space_zero[1:-1])  # исключая первое(верхнее) и последнее(нижнее) поля
# количество пробелов на 1 меньше, чем количество строк, но total_space_row_count содержит верхнее и нижнее поля
average_line_spacing = float(total_space_row_count) / lines_having_midzone_count
average_letter_size = float(midzone_row_count) / lines_having_midzone_count
# Размер букв - это их высота, не ширина!!!
LETTER_SIZE = average_letter_size
# предотвращение ошибок
if (average_letter_size == 0): average_letter_size = 1
# Мы не можем напрямую воспринимать average_line_spacing как межстрочный интервал. Мы должны взять средний_строчный интервал относительно average_letter_size
# Межстрочный интервал будет считаться относительно размера букв
relative_line_spacing = average_line_spacing / average_letter_size
LINE_SPACING = relative_line_spacing

# Верхнее поле также берется относительно среднего размера букв почерка.
relative_top_margin = float(VerhPoleCount) / average_letter_size
verh_pole = relative_top_margin

print ("Средний размер букв: ", (average_letter_size))
print ("Верхнее поле(относительно размера букв): ", (relative_top_margin))
print ("Межстрочный интервал(относительно размера букв): ", (relative_line_spacing))

# Ищем расстояние между словами
width = thresh1.shape[1]
space_zero = []  # хранит количество пробелов между словами
words = []  # 2D список с координатами слов
# мы ищем слова, глядя на появление нулей в вертикальной проекции
for i, line in enumerate(lines):
    extract = thresh1[line[0]:line[1], 0:width]  # y1:y2, x1:x2
    vp = verticalProjection(extract)

    wordStart = 0
    wordEnd = 0
    spaceStart = 0
    spaceEnd = 0
    indexCount = 0
    setWordStart = True
    setSpaceStart = True
    includeNextSpace = True
    spaces = []

    # исследуем вертикальную проекцию
    for j, sum in enumerate(vp):
        # сумма, равная 0, означает пробел
        if (sum == 0):
            if (setSpaceStart):
                spaceStart = indexCount
                setSpaceStart = False  # spaceStart будет устанавливаться один раз для каждого начала пробела
            indexCount += 1
            spaceEnd = indexCount
            if (j < len(vp) - 1):  # это условие необходимо, чтобы избежать ошибки выхода индекса массива за пределы
                if (vp[j + 1] == 0):  # если следующая вертикальная проекция равна 0, продолжаем считать, что это пробел
                    continue

            # мы игнорируем пробелы, размер которых меньше половины среднего размера букв
            if ((spaceEnd - spaceStart) > int(LETTER_SIZE / 2)):
                spaces.append(spaceEnd - spaceStart)

            setSpaceStart = True  # в следующий раз, когда мы встретим 0, это начало другого пробела, поэтому мы устанавливаем новый spaceStart

        # сумма больше 0 означает, что это слово
        if (sum > 0):
            if (setWordStart):
                wordStart = indexCount
                setWordStart = False  # wordStart для каждого нового слова устанавливаем снова
            indexCount += 1
            wordEnd = indexCount
            if (j < len(vp) - 1):  # предотвращение ошибки выхода за пределы массива
                if (vp[j + 1] > 0):  # если следующая горизонтальная проекция> 0, продолжаем считать, что это слово
                    continue

            # добавляем координаты каждого слова: y1, y2, x1, x2 в 'words'
            # игнорируем те, высота которых меньше половины среднего размера букв
            # это исключает точки, запятые и т.п.
            count = 0
            for k in range(line[1] - line[0]):
                row = thresh1[line[0] + k:line[0] + k + 1, wordStart:wordEnd]  # y1:y2, x1:x2
                if (np.sum(row)):
                    count += 1
            if (count > int(LETTER_SIZE / 2)):
                words.append([line[0], line[1], wordStart, wordEnd])

            setWordStart = True  # в следующий раз, когда мы встретим значение> 0, это будет начало другого слова, поэтому мы устанавливаем новый wordStart

    space_zero.extend(spaces[1:-1])

# подсчёт пробелов и их длины
space_columns = np.sum(space_zero)
space_count = len(space_zero)
if (space_count == 0):
    space_count = 1
average_word_spacing = float(space_columns) / space_count
relative_word_spacing = average_word_spacing / LETTER_SIZE
print ("Средний интервал между словами: ", (average_word_spacing))
print ("Средний интервал между словами относительно среднего размера букв:", (relative_word_spacing))

print("Ваш характер на основании полученных данных: ")
if (angle_size < -0.28):
    print("Вы оптимистичный, целеустремленный и уверенный в себе человек.")
elif (angle_size > 0.28):
    print("Вы скептик, трезво оцениваете себя и свои действия.")
else:
    print("Вы уравновешенный человек, который трезво смотрит на мир.")
if (VerhPoleCount > 50):
    print("У Вас отличный вкус, вы хорошо разбираетесь в искусстве и цените красоту.")
elif (VerhPoleCount > 20):
    print("Вы благоразумны, рассудительны и рациональны.")
else:
    print("Вы всегда стремитесь получить максимум из имеющихся возможностей.")
if (average_letter_size > 25):
    print(
        "Вы общительный человек, у вас есть лидерские способности. Вы чётко стоите на своём и умеете убеждать других людей.")
elif (average_letter_size > 18):
    print("Вы спокойный человек, который соблюдает баланс между личной и общественной жизнью.")
else:
    print("Вы умеете сосредотачиваться на нужных вещах. Вы сдержанный человек, который редко проявляет агрессию.")
if (relative_top_margin >= 2):
    print("Вы щедрый и альтруистичный человек.")
elif (relative_top_margin >= 1):
    print("Вы открыты к сотрудничеству с другими людьми и готовы помочь им, но не во вред себе.")
else:
    print("Вы умеете концентрироваться на своих целях и достигать их.")
if (relative_line_spacing > 4):
    print("Вы стремитесь жить 'здесь и сейчас' и брать от жизни максимум.")
elif (relative_line_spacing > 2):
    print(
        "В жизни вы предпочитаете действовать по ситуации: когда необходимо, вы можете придумать план и следовать ему,\nа иногда можете просто наслаждаться моментом.")
else:
    print("Вы хозяйственный и расчетливый человек. Вы всегда оцениваете ситуацию и думаете наперёд.")
if (relative_word_spacing > 2):
    print("Вы открытый и лёгкий на подъём человек. Вы стремитесь показать себя. Вы любите приключения.")
elif (relative_word_spacing > 1):
    print("Вы соблюдаете баланс, совмещая осторожность с жаждой к приключениям. Вы стабильный и надёжный человек.")
else:
    print(
        "Вы осторожны и бережливы. Вы доверяете лишь небольшому кругу людей. Вы предпочитаете полагаться на разум, \nа не на чувства")
