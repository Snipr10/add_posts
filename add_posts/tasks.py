import requests

from add_posts.celery.celery import app
from bs4 import BeautifulSoup
from core import models
from core.helpers import get_proxy, find_value
from django.utils import timezone


@app.task
def start_parsing_url():
    print("a")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Safari/537.36',
    }
    proxy = get_proxy()
    if proxy is None:
        return
    print(proxy)
    proxies = {'https': 'https://{}:{}@{}:{}'.format(proxy.login, proxy.password, proxy.host, str(proxy.port))}
    post_url = \
        models.PostUrl.objects.filter(is_ready=False, is_successful=True,
                                      is_parsing=False).order_by('added_date').first()
    print("post_url" + str(post_url.id))
    if post_url is not None:
        post_url.is_parsing = True
        post_url.save()
        res = None
        try:
            print(post_url.db_post_url)
            res = requests.get(post_url.db_post_url, proxies=proxies, headers=headers).text
            owner_fb_id = find_value(res, '",id:', num_sep_chars=1, separator='"')
            if owner_fb_id is None:
                owner_fb_id = find_value(res, ';id=', num_sep_chars=0, separator='&')
            user_name = find_value(res, ';fref=nf">', num_sep_chars=0, separator='<', is_first=True)
            if user_name is None:
                user_name = find_value(res, '=C-R">', num_sep_chars=0, separator='<', is_first=True)
                if user_name is None:
                    user_name = find_value(res, '<strong class="actor">', num_sep_chars=0, separator='<',
                                           is_first=True)
            text = None
            try:
                beatiful_text = find_value(res, '><div><p>', num_sep_chars=0, separator='</p></div>', is_first=True)
                print(beatiful_text)
                text = BeautifulSoup(
                    find_value(res, '><div><p>', num_sep_chars=0, separator='</p></div>', is_first=True)).text
            except Exception as e:
                print(e)
                pass
            if text is None:
                html = BeautifulSoup(res, 'html')
                text = html.text
            comment = find_value(res, '_comment_count', num_sep_chars=2, separator='"', is_first=True)
            reaction = find_value(res, 'reaction_count:{count:', num_sep_chars=0, separator='}')
            if reaction is None:
                reaction = find_value(res, "like_count:", num_sep_chars=0, separator=',', is_first=True)

            share = find_value(res, '_share_count', num_sep_chars=2, separator='"', is_first=True)
            user = models.User.objects.filter(fb_id=owner_fb_id).first()
            if user is None:
                user_url = find_value(res, '><strong><a href="', num_sep_chars=0, separator='"', is_first=True)
                if user_url is None:
                    user_url = find_value(res, '"actor-link" href="', num_sep_chars=0, separator='"', is_first=True)
                user_url = user_url[:user_url.find(',')]
                user_url = user_url[:user_url.find('"')]
                user_url = user_url[:user_url.find('&')]
                user_url = user_url[:user_url.find('_')]
                user_url = user_url[:user_url.find('?refid=1')]
                if user_url[-1] == "?":
                    user_url = user_url[:-1]
                full_url = "https://www.facebook.com" + user_url
                user = models.User.objects.filter(link=full_url).first()
                if user is None:
                    user = models.User.objects.create(name=user_name, link=full_url, fb_id=owner_fb_id)
            print("user" + str(user.id))
            state = models.PostStat.objects.create(likes=reaction, comments=comment, shares=share)
            print("state" + str(state.id))

            content = models.Content.objects.create(text=text)
            print("content" + str(content.id))
            print("post_url.task_id" + str(post_url.task_id))
            task = models.Task.objects.get(id = int(post_url.task_id))
            print("task" + str(task.id))

            post = models.Post.objects.create(content_id=content.id, task_id=task.id,
                                              user_id=user.id, state_id=state.id)
            print("post " + str(post.id))
            post_url.is_ready = True
            post_url.added_date = timezone.now()
        except Exception as e:
            if "Содержание не найдено" in res:
                post_url.is_successful = False
            elif "Вход на Facebook | Facebook" in res:
                print("sleep proxy")
            else:
                print(e)
        post_url.is_parsing = False
        post_url.save()
