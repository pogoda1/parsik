# Example 1:

INPUT:
<<<
В субботу в пабе «Лондон» организуют музыкальную караоке-вечеринку ТУЦ ЛОТО (https://vk.com/tucloto.kaliningrad) 🎙️ 

🗓️ #31_мая, 16:00
📍 Калининград, пр. Мира, 33

Это не просто игра – это чистые эмоции! Микс старого доброго лото с бочонками и вечеринки. Участники поют и отрываются на полную катушку. 

Стоимость 500 ₽ с человека
👉 регистрация и подробности (https://vk.com/tucloto.kaliningrad)

Подпишись на АНОНС39 (https://t.me/+-cCRoVroPdZiMDYy)
>>>

OUTPUT:
<<<
"data": {
    "eventTitle": "Караоке-вечеринку ТУЦ ЛОТО",
    "eventDescription": "Это не просто игра – это чистые эмоции! Микс старого доброго лото с бочонками и вечеринки. Участники поют и отрываются на полную катушку.",
    "eventDate": [
        {
            "from": ""
        }
    ],
    "eventPrice": [ 0 ],
    "eventCategories": ["charity"],
    "eventThemes": ["science_and_education"],
    "eventAgeLimit": "12",
    "eventLocation": {
      "name": "",
      "address": ""
    },
    "linkSource": ""
  }
>>>

EXPLANATION:

For entries like:

```
Предп культ под оз пш
По Пу 215/1015
Отд 12 128/317
Отд 16 123/529
```

we interpret them as follows:

- The operation is decoded from the first line: "Предп культ" = "Предпосевная культивация", and "оз пш" = "Пшеница озимая товарная".
- The line `По Пу 215/1015` specifies the area processed:
- `215` is taken as `processed_area_day`,
- `1015` is taken as `processed_area_total`.
- Even though multiple departments (`Отд 12`, `Отд 16`) are listed below, only the **first mentioned department_name** (here, `"12"`) is selected for the `department_name` field.

This logic is repeated for each block in the message. Operations like "2-е диск сои под оз пш" are interpreted as "Дискование 2-е" with crop "Пшеница озимая товарная" using similar parsing rules.


---

# Example 2:

INPUT:
<<<
Восход
Посев подсолнечника
День-149га
Всего-351га,67%
Химпрополка рапса
152га, 100%
Первая культивация
Зябис день-180га
Всего-1430га, 76,2%.
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Сев",
            "crop": "Подсолнечник товарный",
            "processed_area_day": 149,
            "processed_area_total": 351,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Гербицидная обработка",
            "crop": "Рапс озимый",
            "processed_area_day": 152,
            "processed_area_total": null,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Культивация",
            "crop": "Рапс озимый",
            "processed_area_day": 180,
            "processed_area_total": 1430,
            "yield_kg_day": null,
            "yield_kg_total": null
        }
    ]
}
>>>

EXPLANATION:
This message contains multiple operations under the department `"Восход"`.

- **Entry 1**:
`"Посев подсолнечника"` is interpreted as `"Сев"` with crop `"Подсолнечник товарный"`.
The values `"День-149га"` and `"Всего-351га"` are used to populate `processed_area_day = 149` and `processed_area_total = 351`.

- **Entry 2**:
`"Химпрополка рапса"` is interpreted as `"Гербицидная обработка"` on crop `"Рапс озимый"`.
Only one area value (`"152га"`) is present, so only `processed_area_day = 152` is filled, and `processed_area_total` is left `null`.

- **Entry 3**:
`"Первая культивация"` is interpreted as `"Культивация"`, not `"1-я междурядная культивация"`, because there is no mention of междурядная or similar terms.
No crop is explicitly mentioned here, so the crop from the **most recent compatible operation** (Entry 2) is reused: `"Рапс озимый"`.
Area values `"день-180га"` and `"всего-1430га"` are used to fill `processed_area_day = 180` and `processed_area_total = 1430`.

---

# Example 3:

INPUT:
<<<
Север
Отд7 пах с св 41/501
Отд20 20/281 по пу 61/793
Отд 3 пах подс.60/231
По пу 231

Диск к. Сил отд 7. 32/352
Пу- 484
Диск под Оз п езубов 20/281
Диск под с. Св отд 10 83/203 пу-1065га
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": null,
            "department_name": "Север",
            "operation": "Пахота",
            "crop": "Свекла сахарная",
            "processed_area_day": 61,
            "processed_area_total": 793,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Север",
            "operation": "Пахота",
            "crop": "Подсолнечник товарный",
            "processed_area_day": 60,
            "processed_area_total": 231,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Север",
            "operation": "Дискование",
            "crop": "Кукуруза кормовая",
            "processed_area_day": 32,
            "processed_area_total": 484,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Север",
            "operation": "Дискование",
            "crop": "Пшеница озимая товарная",
            "processed_area_day": 20,
            "processed_area_total": 281,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Север",
            "operation": "Дискование",
            "crop": "Свекла сахарная",
            "processed_area_day": 83,
            "processed_area_total": 1065,
            "yield_kg_day": null,
            "yield_kg_total": null
        }
    ]
}
>>>

EXPLANATION:

This message contains multiple fieldwork records under the regional department `"Север"`. All `Отд` references are considered part of it, so `department_name = "Север"` for all entries.

**Parsing rules:**

1. **Department inheritance**:
`"Север"` is mentioned first — all following `Отд` entries belong to it.

2. **New entry = new operation**:
Every line with a new operation keyword (`"пах"`, `"диск"`, etc.) starts a new entry. Lines without operations are considered part of the current one.

3. **Area values from "по пу"/"пу-" take priority**:
Use values like `по пу 61/793` or `пу-1065га` for `processed_area_day` / `processed_area_total` if present.

4. **Abbreviation expansion**:
- `"пах"` → `"Пахота"`
- `"диск"` → `"Дискование"`
- `"Оз п"` → `"Пшеница озимая товарная"`
- `"к. Сил"` → `"Кукуруза кормовая"`
- `"с. Св"` → `"Свекла сахарная"`


---

# Example 4:

INPUT:
<<<
Внесение удобрений под рапс отд 7 -138/270
Дисклвание под рапс 40/172
Диск после Кук сил отд 7-32/352 по пу 484га
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": null,
            "department_name": "7",
            "operation": "Внесение минеральных удобрений",
            "crop": "Рапс озимый",
            "processed_area_day": 138,
            "processed_area_total": 270,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "7",
            "operation": "Дискование",
            "crop": "Рапс озимый",
            "processed_area_day": 40,
            "processed_area_total": 172,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "7",
            "operation": "Дискование",
            "crop": "Кукуруза кормовая",
            "processed_area_day": 32,
            "processed_area_total": 484,
            "yield_kg_day": null,
            "yield_kg_total": null
        }
    ]
}
>>>

EXPLANATION:

For the message:

```
Внесение удобрений под рапс отд 7 -138/270
Дисклвание под рапс 40/172
Диск после Кук сил отд 7-32/352 по пу 484га
```

we parse three separate entries because we identify **three distinct operations**.

- In the first line,
- `"Внесение удобрений под рапс"` is interpreted as the operation `"Внесение минеральных удобрений"` with the crop `"Рапс озимый"`.
- `"отд 7 -138/270"` provides:
    - `department_name = "7"`,
    - `processed_area_day = 138`,
    - `processed_area_total = 270`.

- In the second line,
- `"Дисклвание под рапс"` is interpreted as the operation `"Дискование"` and crop `"Рапс озимый"`.
- `"40/172"` gives:
    - `processed_area_day = 40`,
    - `processed_area_total = 172`.
- No department_name is explicitly specified, but since department_name `"7"` is mentioned in both the first and third lines, we **infer** that this operation is also performed by department_name `"7"`.

- In the third line,
- `"Диск после Кук сил"` is interpreted as the operation `"Дискование"` and crop `"Кукуруза кормовая"`.
- `"отд 7-32/352"` provides:
    - `department_name = "7"`,
    - `processed_area_day = 32`,
    - `"по пу 484га"` gives `processed_area_total = 484`.


---

# Example 5:

INPUT:
<<<
10.03 день
2-я подкормка озимых, ПУ "Юг" - 1749/2559
(в т.ч Амазон-1082/1371
Пневмоход-667/1188)

Отд11- 307/307 (амазон 307/307)

Отд 12- 671/671( амазон 318/318; пневмоход 353/353)

Отд 16- 462/1272( амазон 148/437; пневмоход 314/835)

Отд 17- 309/309( амазон 309/309)
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": "03-10",
            "department_name": "Юг",
            "operation": "2-я подкормка",
            "crop": "Пшеница озимая товарная",
            "processed_area_day": 1749,
            "processed_area_total": 2559,
            "yield_kg_day": null,
            "yield_kg_total": null
        }
    ]
}
>>>

EXPLANATION:

The message appears to list multiple lines with department-level details, but in fact it describes a **single field operation**:

- The operation `"2-я подкормка"` is mentioned only once at the beginning of the message, which means there is only **one entry** to be created.
- The crop `"озимых"` (winter crops) is interpreted as `"Пшеница озимая товарная"` by default.
- The `"ПУ "Юг""` segment provides the **summary values** for the entire operation:
- `1749` is the processed area for the day (`processed_area_day`)
- `2559` is the total processed area since the start of the operation (`processed_area_total`)
- All other lines such as `(в т.ч Амазон...)`, `Пневмоход...`, and `Отд 11...` are **department-level breakdowns** and should be ignored in the structured output, as they do not correspond to separate operations.

Therefore, we only extract **one entry**, and take values directly from the `"ПУ"` line. The date `"10.03"` at the beginning of the message applies to the entire entry.


---

# Example 6:

INPUT:
<<<
Уборка свеклы 27.10.день
Отд10-45/216
По ПУ 45/1569
Вал 1259680/6660630
Урожайность 279,9/308,3
По ПУ 1259680/41630600
На завод 1811630/6430580
По ПУ 1811630/41400550
Положено в кагат 399400
Вввезено с кагата 951340
Остаток 230060
Оз-9,04/12,58
Дигестия-14,50/15,05
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": "10-27",
            "department_name": "10",
            "operation": "Уборка",
            "crop": "Свекла сахарная",
            "processed_area_day": 45,
            "processed_area_total": 1569,
            "yield_kg_day": 1259680,
            "yield_kg_total": 6660630
        }
    ]
}
>>>

EXPLANATION:

For the message:

```
Уборка свеклы 27.10.день
Отд10-45/216
По ПУ 45/1569
Вал 1259680/6660630
Урожайность 279,9/308,3
По ПУ 1259680/41630600
На завод 1811630/6430580
По ПУ 1811630/41400550
Положено в кагат 399400
Вввезено с кагата 951340
Остаток 230060
Оз-9,04/12,58
Дигестия-14,50/15,05
```

we extract only **one entry**, because there is a clear and explicit operation: `"Уборка свеклы"` (interpreted as operation `"Уборка"` and crop `"Свекла сахарная"`).

- `"Отд10-45/216"` and `"По ПУ 45/1569"` indicate:
- `department_name = "10"`,
- `processed_area_day = 45`,
- `processed_area_total = 1569`.

- `"Вал 1259680/6660630"` represents the yield in kilograms, so we get:
- `yield_kg_day = 1259680`,
- `yield_kg_total = 6660630`.

Despite the presence of many other numbers and unrelated metrics (e.g., завод, кагат, дигестия), these are treated as **noise** in this context. Only the main entry related to **field harvesting** is extracted.


---

# Example 7:

INPUT:
<<<
Восход
Посев кук-24/252га
24%
Предпосевная культ
Под кук-94/490га46%
СЗРоз пш-103/557га
25%
Подкормка оз рапс-
152га , 100%, подкормка овса-97га, 50%
Довсходовое боронование подсолнечника-524
га, 100%.
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Сев",
            "crop": "Кукуруза товарная",
            "processed_area_day": 24,
            "processed_area_total": 252,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Предпосевная культивация",
            "crop": "Кукуруза товарная",
            "processed_area_day": 94,
            "processed_area_total": 490,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Гербицидная обработка",
            "crop": "Пшеница озимая товарная",
            "processed_area_day": 103,
            "processed_area_total": 557,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Подкормка",
            "crop": "Рапс озимый",
            "processed_area_day": 152,
            "processed_area_total": null,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Подкормка",
            "crop": "Овес",
            "processed_area_day": 97,
            "processed_area_total": null,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": null,
            "department_name": "Восход",
            "operation": "Боронование довсходовое",
            "crop": "Подсолнечник товарный",
            "processed_area_day": 524,
            "processed_area_total": null,
            "yield_kg_day": null,
            "yield_kg_total": null
        }
    ]
}
>>>

EXPLANATION:
This message includes multiple operations, all under the department `"Восход"`.

- For the **first three records**, both `processed_area_day` and `processed_area_total` are explicitly mentioned in the message using the `x/y` format (e.g., `"24/252га"`, `"94/490га"`, `"103/557га"`), so both fields are filled.

- For the **remaining three records**, only one area value is mentioned (e.g., `"152га"`, `"97га"`, `"524га"`), which is interpreted as `processed_area_day`, while `processed_area_total` is left as `null`.

Other interpretation rules applied:

- `"Посев кук"` → `"Сев"` operation, `"Кукуруза товарная"` as crop (defaulted to товарная type since no subtype is specified).
- `"Под кук"` under `"Предпосевная культ"` is expanded to `"Предпосевная культивация"` with crop `"Кукуруза товарная"`.
- `"СЗР оз пш"` is interpreted as `"Гербицидная обработка"` on `"Пшеница озимая товарная"`, based on abbreviation rules for СЗР.
- `"Подкормка оз рапс"` and `"подкормка овса"` are treated as separate `"Подкормка"` operations on `"Рапс озимый"` and `"Овес"` respectively.
- `"Боронование довсходовое подсолнечника"` is mapped to the corresponding operation and crop.

Percentage values like `"24%"`, `"46%"`, or `"100%"` are ignored, as they are not part of the structured schema.

---

# Example 8:

INPUT:
<<<
30.03.25г Мир.
Предпосевная культивация под подсолнечник 50/97/609 - 14%
Сев подсолнечника 17/47/659 - 6%
2-я подкормка озимой пшеницы 371/5118/166 - 97%
Прикат мн тр под оз пш 60/60/100
На данный момент осадки в 2х районах до 3мм
>>>

OUTPUT:
<<<
{
    "entries": [
        {
            "date": "03-30",
            "department_name": "Мир",
            "operation": "Предпосевная культивация",
            "crop": "Подсолнечник товарный",
            "processed_area_day": 50,
            "processed_area_total": 97,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": "03-30",
            "department_name": "Мир",
            "operation": "Сев",
            "crop": "Подсолнечник товарный",
            "processed_area_day": 17,
            "processed_area_total": 47,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": "03-30",
            "department_name": "Мир",
            "operation": "2-я подкормка",
            "crop": "Пшеница озимая товарная",
            "processed_area_day": 371,
            "processed_area_total": 5118,
            "yield_kg_day": null,
            "yield_kg_total": null
        },
        {
            "date": "03-30",
            "department_name": "Мир",
            "operation": "Прикатывание посевов",
            "crop": "Пшеница озимая товарная",
            "processed_area_day": 60,
            "processed_area_total": 60,
            "yield_kg_day": null,
            "yield_kg_total": null
        }
    ]
}
>>>

EXPLANATION:
This message includes several operations, each with area values written in the `x/y/z` format. The interpretation follows these rules:

- `x` is used as `processed_area_day`
- `y` is used as `processed_area_total`
- `z` is **ignored** because it typically indicates a **remaining area** (остаток), which is **not part of the structured schema** and should not be included

**Examples from the message:**

- `"Предпосевная культивация под подсолнечник 50/97/609"` →
`processed_area_day = 50`, `processed_area_total = 97`, `609` is ignored

- `"Сев подсолнечника 17/47/659"` →
`processed_area_day = 17`, `processed_area_total = 47`, `659` is ignored

- `"2-я подкормка озимой пшеницы 371/5118/166"` →
`processed_area_day = 371`, `processed_area_total = 5118`, `166` is ignored

- `"Прикат мн тр под оз пш 60/60/100"` is interpreted as the operation `"Прикатывание посевов"` on the crop `"Пшеница озимая товарная"`, because:
- The phrase expands to: **"Прикатывание посевов многолетних трав под озимую пшеницу"**
- In such constructions, the **second mentioned crop** (here, озимая пшеница) is treated as the **target crop** and is assigned to the `crop` field

Area values are:
- `processed_area_day = 60`
- `processed_area_total = 60`
- `100` is ignored as it denotes the remaining area

The department name `"Мир"` is stated at the beginning and applies to **all entries** in the message.

Lines like `"осадки в 2х районах до 3мм"` contain environmental context and are **ignored** as they do not represent operations from the schema.
