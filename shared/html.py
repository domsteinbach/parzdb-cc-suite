from bs4 import BeautifulSoup


def get_as_element(comment_element, element='span'):
    class_list = comment_element.style.classes
    class_str = ' '.join(class_list) if class_list else None
    soup = BeautifulSoup(features="html.parser")
    tag = soup.new_tag(element)
    if class_str:
        tag['class'] = class_str
    tag.string = comment_element.text
    return str(tag)

def get_as_dynamic_hyperlink(comment_element):
    soup = BeautifulSoup(features="html.parser")
    link_tag = soup.new_tag("a", href=comment_element.dynamic_dreissiger_href, target="_blank")
    link_tag.string = comment_element.text
    return str(link_tag)

def get_as_a(comment_element):
    soup = BeautifulSoup(features="html.parser")
    link_tag = soup.new_tag("a", href=comment_element.h_ref, target="_blank")
    for sub_element in comment_element.elements:
        link_tag.append(BeautifulSoup(get_as_element(sub_element), "html.parser"))
    return str(link_tag)


def clean_up_html(html_str):
    soup = BeautifulSoup(html_str, "html.parser")

    # Find all spans and iterate over them
    spans = soup.find_all("span")
    for i, span in enumerate(spans):
        # Check if this span has only a single space as text
        if span.string and span.string.strip() == "":
            if i > 0 and spans[i - 1].name == "span":
                # Append this space to the previous span
                spans[i - 1].append(" ")
            # Remove the current span
            span.decompose()

    return str(soup)

