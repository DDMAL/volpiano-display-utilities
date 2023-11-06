import json


def read_test_cases():
    with open("tests/alignment_test_cases.json", encoding="ascii") as test_case_json:
        test_cases = json.load(test_case_json)
    name_and_exp_results = []
    for test_case in test_cases:
        name_and_exp_results.append(
            (test_case["case_name"], test_case["expected_result"])
        )
    return name_and_exp_results


def create_html_string(cases):
    all_test_html = """<head>
                    <link href="static/volpiano.css" rel="stylesheet" media="screen">
                    </head><body>"""
    for case_name, chant in cases:
        chant_html = f'<div style="display:flex"><h4>{case_name}</h4>'
        for txt, vol in chant:
            chant_html += f"""<span style="float: left"><div style="font-family: volpiano; font-size: 36px; white-space: nowrap">{vol}</div>
                        <div class="mt-2" style="font-size: 12px; "><pre>{txt}</pre></div>
                        </span>
                        """
        chant_html += "</div>"
        all_test_html += chant_html
    all_test_html += "</body>"
    return all_test_html


if __name__ == "__main__":
    cases = read_test_cases()
    html = create_html_string(cases)
    with open("tests/alignment_test_cases.html", "w", encoding="utf-8") as html_file:
        html_file.write(html)
