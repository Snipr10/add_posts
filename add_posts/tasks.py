import json
from datetime import timedelta, datetime

import requests

from add_posts.celery.celery import app
from bs4 import BeautifulSoup
from core import models
from core.helpers import get_proxy, find_value
from django.utils import timezone


@app.task
def start_parsing_url():
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
            task = models.Task.objects.get(id=int(post_url.task_id))
            print("task" + str(task.id))
            #
            post = models.Post.objects.create(content=content, task=task,
                                              user=user, stat=state)
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


@app.task
def update_proxy():
    print("update_proxy")
    key = models.Keys.objects.all().first().proxykey
    new_proxy = requests.get("https://api.best-proxies.ru/proxylist.json?key=%s&twitter=1&type=http&speed=1" % key)

    proxies = []
    for proxy in json.loads(new_proxy.text):
        host = proxy['ip']
        port = proxy['port']
        if not models.Proxy.objects.filter(host=host, port=port).exists():
            proxies.append(models.Proxy(host=host, port=port, login="test", password="test"))
    models.Proxy.objects.bulk_create(proxies, batch_size=200, ignore_conflicts=True)


@app.task
def delete_bad_worker_credentials():
    print("delete")
    for cred in models.WorkCredentials.objects.filter(locked=True):
        try:
            proxy = cred.proxy
            if proxy.login == "sergmga_gmail_com" or \
                    not check_proxy("http://www.zahodi-ka.ru/proxy/check/?p=http://%s:%s" % (proxy.host,
                                                                                             str(proxy.port))):
                account = cred.account
                account.available = True
                account.banned = False
                account.save()
                proxy.available = False
                proxy.save()
            cred.delete()
        except Exception:
            pass


@app.task
def check_not_available_accounts():
    # maybe 100 ??
    for account in models.Account.objects.filter(available=False).order_by("-id"):
        print("account.id")
        print(account.id)
        if check_accounts(account.login, account.password, attempt=0):
            account.available = True
            account.banned = False
            account.save()


def check_proxy(url, attempt=0):
    if '<ok>' in requests.get(url).text:
        print("check_proxy True " + str(attempt))
        return True
    else:
        print("check_proxy False " + str(attempt))
        if attempt >= 5:
            return False
        else:
            return check_proxy(url, attempt + 1)

    # TEST PROXY
    # res_er = requests.get("http://www.zahodi-ka.ru/proxy/check/?p=http://181.118.145.146:9991")
    # res_ok = requests.get("http://www.zahodi-ka.ru/proxy/check/?p=http://181.118.145.146:999")
    #
    # if '<er>' in res_er.text:
    #     print("res_er bad")
    # if '<ok>' in res_er.text:
    #     print("res_er ok")
    # if '<er>' in res_ok.text:
    #     print("res_ok bad")
    # if '<ok>' in res_ok.text:
    #     print("res_ok ok")

    # queryset._raw_delete(queryset.db)


def get_available_proxy():
    proxy = models.Proxy.objects.filter(available=True, expirationDate__gte=datetime.now()).order_by(
        "id").last()

    if proxy is not None:
        # if check_proxy("http://www.zahodi-ka.ru/proxy/check/?p=http://%s:%s" % (proxy.host,
        #                                                                         str(proxy.port))):
        return proxy
        # else:
        #     return get_available_proxy()
    else:
        return None


def check_accounts(email, password, attempt=0):
    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    proxy = get_available_proxy()
    if proxy is None:
        return
    print("proxy.id")
    print(proxy.id)
    proxy_str = f"{proxy.login}:{proxy.password}@{proxy.host}:{proxy.port}"
    print(proxy_str)
    proxies = {'http': f'http://{proxy_str}', 'https': f'https://{proxy_str}'}
    try:
        session.proxies.update(proxies)
        response = session.get('https://m.facebook.com')

        # login to Facebook
        response = session.post('https://m.facebook.com/login.php', data={
            'email': email,
            'pass': password
        }, allow_redirects=False)

        # If c_user cookie is present, login was successful
        if 'c_user' in response.cookies:
            print("account ok " + email)
            return True
        else:
            print("account disable " + email)

            return False
    except Exception:
        proxy.available = False
        proxy.save()
        if attempt < 5:
            print("account Exception " + email)

            return check_accounts(email, password, attempt + 1)
        else:
            print("account Exception disable " + email)
            return False
