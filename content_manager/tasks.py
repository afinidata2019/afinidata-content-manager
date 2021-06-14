from posts.models import PostLocale, Post
from celery import shared_task
import boto3
import json
import base64
import requests
import csv

@shared_task
def add(x, y):
    return x + y

@shared_task
def translate_locale_posts(language_origin = 'en',
                           language_destination = 'ar',
                           destination_locale = 'ar_AE'):
    def generate_csv(list, filename):
        keys = list[0].keys()
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(list)
    def get_post_from_wordpress(post_slug):
        import requests
        r = requests.get('https://activities.afinidata.com/wp-json/wp/v2/posts?slug=%s' % (post_slug))
        #get imitating-animal-sounds
        post = None
        try:
            post = r.json()[0]
        except:
            raise Exception(dict(request = 'https://activities.afinidata.com/wp-json/wp/v2/posts?slug=%s' % (post_slug)))
        return post
    def save_post_wordpress(post_slug, post_title, post_content):
        url_srcdest = "https://activities.afinidata.com/wp-json/wp/v2/posts/"
        code = 'bHVjaTp3TWFLIEIxbFMgTFBDNiBqamFxIHl2UmMgSjEzUwo='#str(base64.b64encode(b'luci:wMaK B1lS LPC6 jjaq yvRc J13S'), 'utf-8')
        headers = {'Content-Type': 'application/json',
                 'Authorization': 'Basic %s' % (code),
                 'Username': 'luci',
                 'Password': '%s' % (code)}
        data = \
            {
                "title" : post_title,
                "content" : post_content,
                "status" : "draft",
                "slug" : post_slug
            }
        response = requests.post(url_srcdest, data=json.dumps(data), headers=headers)
        if response.status_code < 199 or response.status_code > 300:
            raise Exception(dict(code = response.status_code, response = response.json(), request = data))
        return 'https://activities.afinidata.com/%s/' % (post_slug)
    translate = boto3.client(service_name='translate', region_name='us-east-2', use_ssl=True)
    #Get the URLs of posts that language_origin matches PostLocale,
    #but have no language_destination PostLocale
    done = PostLocale.objects.filter(lang=language_destination)
    excluded_posts = set()
    for d in done:
        excluded_posts.add(d.post)
    post_locales_to_translate = PostLocale.objects \
      .exclude(post__in=excluded_posts) \
      .filter(lang = language_origin)
    # Get al posts that doesnt have an lenguage_destination translation
    done = Post.objects.filter(postlocale__lang=language_destination)
    excluded_posts = set()
    for d in done:
        excluded_posts.add(d.name)
    post_to_translate = Post.objects.exclude(name__in=excluded_posts)

    translated_posts = []
    for post in post_to_translate:
        post_name = post.content \
          .replace('https://activities.afinidata.com/', '') \
          .replace('/', '')
        #Get the content from the wordpress API
        wordpress_post = get_post_from_wordpress(post_slug = post_name)
        translated_content = translate \
                            .translate_text(Text = wordpress_post['content']['rendered'],
                                            SourceLanguageCode = language_origin,
                                            TargetLanguageCode = language_destination)
        translated_title = translate \
                           .translate_text(Text = post.name,
                                           SourceLanguageCode = language_origin,
                                           TargetLanguageCode = language_destination)
        #save_new_post_in_wordpress
        url = save_post_wordpress(post_slug = language_destination+'-%s' % (post_name),
                                  post_title = translated_title['TranslatedText'],
                                  post_content = translated_content['TranslatedText'])
        translated_posts.append(dict(post = post.id,
                                     post_name = post.name,
                                     url = url))
    generate_csv(list = translated_posts, filename = 'output.csv')
    return dict(translated = len(post_to_translate), posts = translated_posts)
