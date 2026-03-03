import sys
from html.parser import HTMLParser
from collections import defaultdict

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.imgs = []
        self.anchors = []
        self.inputs = []
        self.labels_for = set()
        self.headings = []
        self.has_title = False
        self.html_lang = None
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.html_lang = attrs.get('lang')
        if tag == 'title':
            self.in_title = True
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'img':
            self.imgs.append({'src': attrs.get('src',''), 'alt': attrs.get('alt'), 'role': attrs.get('role')})
        if tag == 'a':
            self.anchors.append({'href': attrs.get('href',''), 'text': attrs.get('aria-label') or ''})
        if tag in ('input','textarea','select'):
            self.inputs.append({'tag': tag, 'id': attrs.get('id'), 'type': attrs.get('type')})
        if tag == 'label':
            if 'for' in attrs:
                self.labels_for.add(attrs['for'])
        if tag in ('h1','h2','h3','h4','h5','h6'):
            self.headings.append(tag)

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            if data.strip():
                self.has_title = True


def main(path):
    p = MyHTMLParser()
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    p.feed(content)

    issues = []

    # lang attribute
    if not p.html_lang:
        issues.append('Missing lang attribute on <html> element.')

    # title
    if not p.has_title:
        issues.append('Missing or empty <title> tag.')

    # duplicate IDs
    dup = [id for id, count in ((i, p.ids.count(i)) for i in set(p.ids)) if count > 1]
    if dup:
        issues.append(f'Duplicate id attributes found: {dup}')

    # images missing alt (except purely decorative with role=presentation)
    imgs_missing_alt = []
    for img in p.imgs:
        if (not img.get('alt')) and img.get('role') != 'presentation':
            imgs_missing_alt.append(img.get('src') or '(no src)')
    if imgs_missing_alt:
        issues.append(f'Images missing alt attribute (or empty): {imgs_missing_alt}')

    # inputs without label-for
    inputs_without_label = []
    for inp in p.inputs:
        if inp.get('id'):
            if inp['id'] not in p.labels_for:
                inputs_without_label.append(inp)
        else:
            inputs_without_label.append(inp)
    if inputs_without_label:
        issues.append(f'Form controls missing associated <label for="id"> (ids or unlabeled): {inputs_without_label}')

    # anchors with href '#' or javascript:void(0)
    bad_anchors = [a['href'] for a in p.anchors if not a['href'] or a['href'].strip() in ('#','javascript:void(0)','javascript:void(0);')]
    if bad_anchors:
        issues.append(f'Anchors with empty or placeholder hrefs: {bad_anchors}')

    # heading order basic check: ensure at least one h1
    if 'h1' not in p.headings:
        issues.append('No <h1> heading found on page.')

    # Output
    if issues:
        print('HTML LINT REPORT — issues found:\n')
        for it in issues:
            print('- ' + it)
        sys.exit(1)
    else:
        print('HTML LINT REPORT — no obvious issues found.')
        sys.exit(0)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
    main(path)
