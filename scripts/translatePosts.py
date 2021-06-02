# Create WordPress pages with translated content from already existing WordPress pages registered in Post
# We obtain only the plain text from the page to translate, in order to retain unchanged the HTML tags.
from posts.models import PostLocale, Post
import boto3
import json
import base64
import requests
import csv
import time
import os

AFINICONTENT_URL = "https://afinicontent.com"

def add(x, y):
    return x + y

def translate_locale_posts(language_origin = 'en',
                           language_destination = 'pt',
                           locale_destination = 'pt_PT'):
    """
        Uploads featured media to wordpress and get link
    """
    def upload_img_featured(image_path):
        try:
            code = str(base64.b64encode(b'luci:NGV8 3x5L kZ0m QENi qZEA XavL'),'utf-8')
            url= AFINICONTENT_URL + '/wp-json/wp/v2/media'
            data = open(image_path, 'rb').read()
            headers = {'Content-Type': 'application/json',
                    'Authorization': 'Basic %s' % (code),
                    'Username': 'luci',
                    'Password': '%s' % (code)}
            res = requests.post(url=url,
                                data=data,
                                headers=headers)

            new_dict=res.json()
            # new_id= new_dict.get('id')
            link = new_dict.get('guid').get("rendered")
            return link
        except FileNotFoundError:
            return None

    def generate_csv(list, filename):
        keys = list[0].keys()
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(list)

    def get_post_from_wordpress(post_slug):
        import requests
        r = requests.get('%s/wp-json/wp/v2/posts?slug=%s' % (AFINICONTENT_URL, post_slug))
        #get imitating-animal-sounds
        post = None
        try:
            post = r.json()[0]
        except:
            r = requests.get('%s/wp-json/wp/v2/posts?slug=%s' % (AFINICONTENT_URL, post_slug[3:]))
            try:
                post = r.json()[0]
            except:
                raise Exception(dict(request = '%s/wp-json/wp/v2/posts?slug=%s' % (AFINICONTENT_URL, post_slug)))
        return post

    def save_post_wordpress(post_slug, post_title, post_content, featured_media):
        url_srcdest = AFINICONTENT_URL + "/wp-json/wp/v2/posts/"
        # code = 'bHVjaTp3TWFLIEIxbFMgTFBDNiBqamFxIHl2UmMgSjEzUwo='#str(base64.b64encode(b'luci:wMaK B1lS LPC6 jjaq yvRc J13S'), 'utf-8')

        code = str(base64.b64encode(b'luci:NGV8 3x5L kZ0m QENi qZEA XavL'),'utf-8')

        headers = {'Content-Type': 'application/json',
                 'Authorization': 'Basic %s' % (code),
                 'Username': 'luci',
                 'Password': '%s' % (code)}
        data = \
            {
                "title" : post_title,
                "content" : post_content,
                "status" : "draft",
                "slug" : post_slug,
            }
        if featured_media is not None:
            data["featured_media"] = featured_media

        response = requests.post(url_srcdest, data=json.dumps(data), headers=headers)

        if response.status_code < 199 or response.status_code > 300:
            raise Exception(dict(code = response.status_code, response = response.json(), request = data))

        return '%s/%s/' % (AFINICONTENT_URL, post_slug)

    #Get the URLs of posts that language_origin matches PostLocale,
    #but have no language_destination PostLocale

    posts_array_id = [
       '517','518','519','520','521','583','584','522','523','524','525','526','532','533','534','535','536','537','539','540','541','982','542','543','544','545','546','547','548','549','550','869','551','552','983','553','554','555','556','557','558','559','560','562','563','585','586','587','588','589','590','591','856','867','984','592','985','593','594','595','596','597','598','599','600','601','602','603','604','605','606','607','608','609','610','611','612','613','616','618','619','620','621','622','623','624','626','627','628','629','630','631','632','633','634','635','636','637','638','639','640','641','642','643','644','645','646','647','648','652','653','654','655','656','657','658','659','660','661','662','713','721','724','725','726','727','728','730','734','735','756','757','758','759','760','761','663','664','665','666','667','668','669','670','671','672','673','674','675','676','677','678','679','680','681','683','684','685','687','689','690','691','692','693','694','695','696','697','698','699','701','704','702','703','712','705','682','700','706','1139'
    ]

    done = PostLocale.objects.filter(lang=language_destination)
    excluded_posts = set()

    for d in done:
        excluded_posts.add(d.post)

    post_locales_to_translate = PostLocale.objects \
      .exclude(post__in=excluded_posts) \
      .filter(lang = language_origin, post_id__in=posts_array_id)

    # # Get al posts that doesnt have an lenguage_destination translation
    done = Post.objects.filter(postlocale__lang=language_destination)
    excluded_posts = set()

    for d in done:
        excluded_posts.add(d.id)

    post_to_translate = Post.objects.exclude(id__in=excluded_posts) \
        .filter(content__startswith=AFINICONTENT_URL, id__in=posts_array_id)

    #post_to_translate = Post.objects.filter(id=291, postlocale__lang=language_origin)
    translated_posts = []

    # use imagen from wordpres post
    use_image_from_wp = False

    for post in post_to_translate:
        current_post_locale = PostLocale.objects.filter(post_id=post.id, lang=language_origin).first()

        post_name = post.content \
          .replace(AFINICONTENT_URL+'/', '') \
          .replace('/', '')

        current_slug = current_post_locale.link_post.split("/")[3]

        # Get the content from the wordpress API
        wordpress_post = get_post_from_wordpress(post_slug = current_slug)

        # Separate text to avoid translating HTML tags, we only need to translate plain text
        text_html = " " + wordpress_post['content']['rendered'].replace("^", "")
        title = post.name
        delimiter = "^"
        tags_array = []
        plain_text_array = []
        i = 0

        while i < len(text_html):
            text = ""
            while i < len(text_html) and text_html[i] != "<":
                text += text_html[i]
                i += 1
            plain_text_array.append(text)
            tag = ""
            while i < len(text_html) and text_html[i] != ">":
                tag += text_html[i]
                i += 1
            if i < len(text_html):
                tag += text_html[i]
                i += 1
            tags_array.append(tag)

        # plain_text = title + delimiter + (" "+delimiter+" ").join(plain_text_array)

        plain_text = (" "+delimiter+" ").join(plain_text_array)

        # Translate
        translate = boto3.client(service_name='translate', region_name='us-east-2', use_ssl=True)

        # Wait to avoid ThrottlingException
        time.sleep(5)

        plain_text = translate \
            .translate_text(Text=plain_text,
                            SourceLanguageCode=language_origin,
                            TargetLanguageCode=language_destination)['TranslatedText']

        # Join again the plain text with the HTML structure
        # title = plain_text.split(delimiter)[0]
        # plain_text_array = plain_text.split(delimiter)[1:]
        plain_text_array = plain_text.split(delimiter)

        translated_text_html = ""

        for i in range(len(plain_text_array)):
            if i < len(plain_text_array):
                translated_text_html += plain_text_array[i]
            if i < len(tags_array):
                translated_text_html += tags_array[i]


        if use_image_from_wp:
            image_post_url = wordpress_post['featured_media']
        else:
            image_post_url = upload_img_featured(post.thumbnail)

        #Create the new translated Wordpress Page, save_new_post_in_wordpress
        url = save_post_wordpress(post_slug = language_destination+'-%s' % (post_name),
                                  post_title = title,
                                  post_content = translated_text_html,
                                  featured_media=image_post_url)
        # #save postLocale
        new_post_locale = PostLocale(lang=language_destination,
                                   locale=locale_destination,
                                   title=title,
                                   plain_post_content=translated_text_html,
                                   link_post=url,
                                   post_id=post.id)
        new_post_locale.save()

        print("ID:", post.id, "Translated:", title, "Image:", "url: ", url)

        translated_posts.append(dict(post = post.id,
                                     post_locale=new_post_locale.id,
                                     post_name = post.name,
                                     url = url))

        generate_csv(list = translated_posts, filename = 'output.csv')

    return dict(translated = len(post_to_translate), posts = translated_posts)


translate_locale_posts(language_origin='en', language_destination='pt', locale_destination = 'pt_PT')
