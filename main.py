import requests
import time

class YaUploader:
    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def adr_parser(self, file_path):
        """Метод получает имя файла из пути к нему"""
        adr_split = file_path.replace("\\", " ")
        adr_list = adr_split.split()
        return adr_list[-1]

    def get_upload_link(self, disk_file_path, src=None):
        """Получаем ссылку для загрузки файла на Я.Диск"""
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        if src is None:
            params = {'path': disk_file_path, 'overwrite': 'true'}
        else:
            params = {'url': src, 'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload(self, file_path):
        """Метод загруджает файл file_path на Я.Диск"""
        filename = self.adr_parser(file_path)
        href = self.get_upload_link(disk_file_path=filename).get('href', '')
        response = requests.put(href, data=open(file_path, 'rb'))
        response.raise_for_status()
        if response.status_code == 201:
            return f'File "{self.adr_parser(file_path)}" was created successfully'

    def link_upload(self, src, disk_file_path):
        """Метод выполняет загрузку на Я.Диск по URL"""
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.get_headers()
        params = {
            'path': disk_file_path,
            'url': src,
            'disable_redirects': 'false'}
        response = requests.post(upload_url, headers=headers, params=params)
        answer = response.status_code
        if answer == 401:
            raise AttributeError
        elif answer == 507:
            raise ImportError
        elif answer == 202:
            print('Файл', disk_file_path, 'успешно загружен')


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version='5.131'):
        self.token = token
        self.version = version
        self.params = {
            'access_token': self.token,
            'v': self.version
        }
        response = requests.get(self.url + 'users.get', self.params).json()
        if 'response' in response:
            self.owner_id = response['response'][0]['id']
        elif 'error' in response:
            if response['error']['error_code'] == 5:
                raise ValueError

    def get_albums(self, owner_id=None):
        """Метод позволяет узнать названия альбомов пользователя"""
        if owner_id is None:
            owner_id = self.owner_id
        album_url = self.url + 'photos.getAlbums'
        album_params = {
            'owner_id': owner_id,
            'need_system': 1,
        }
        res = requests.get(album_url, params={**self.params, **album_params}).json()
        if 'response' in res:
            return res['response']['items']
        elif 'error' in res:
            if res['error']['error_code'] == 15:
                albs = [
                    {'id': -6, 'title': 'Фотографии с моей страницы'},
                    {'id': -7, 'title': 'Фотографии на моей стене'},
                    {'id': -15, 'title': 'Сохранённые фотографии'},
                    {'id': -9000, 'title': 'Фотографии со мной'}
                ]
                return albs

    def get_photos(self, album_id, owner_id=None, ):
        """Метод выдаёт подробную информацию о фото из альбома 'album_id' """
        if owner_id is None:
            owner_id = self.owner_id
        photo_url = self.url + 'photos.get'
        photo_params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'extended': 1,
            'count': 1000
        }
        photo_info = requests.get(photo_url, params={**self.params, **photo_params}).json()
        if 'response' in photo_info:
            return photo_info['response']['items']
        elif photo_info['error']['error_code'] == 100:
            raise FileExistsError
        elif photo_info['error']['error_code'] == 200:
            raise FileNotFoundError

    def decomposer(self, album_id):
        """Метод сортирует фото по лайкам """
        photos_list = self.get_photos(album_id)
        attrib_list = []
        for foto in photos_list:
            attrib = {
                'likes': foto['likes']['count'],
                'size': foto['sizes'][-1]['type'],
                'src': foto['sizes'][-1]['url']
            }
            attrib_list.append(attrib)
        sorted_by_likes_list = sorted(attrib_list, key=lambda i: i['likes'], reverse=True)
        return sorted_by_likes_list


def cycle(yandex, vk, album_id):
    """Функция выгружает фото из альбома "album_id" на Я.Диск в корень, присваивая имена по количеству лайков """
    photo_list = vk.decomposer(album_id)
    for photo in photo_list:
        file_path = "/photos/" + "photo_" + str(time.time()) + "_" + str(photo["likes"]) + ".jpg"
        yandex.link_upload(photo['src'], file_path)


def show_album(vk):
    """Функция выводит id и названия доступных для выгрузки альбомов"""
    album_list = vk.get_albums()
    # print(album_list)
    print('Доступные для выгрузки альбомы:')
    for alb in album_list:
        print('id:', alb['id'], '-->', alb['title'])
    print()


if __name__ == '__main__':
    while True:
        try:
            ya_token = input("Введите токен для Я.Диска: ")
            vk_token = input('Введите токен для ВКонтакте: ')
            uploader = YaUploader(ya_token)
            vk_client = VkUser(vk_token)
            my_albums = show_album(vk_client)
            album = input('Выберите альбом для выгрузки: ')
            cycle(uploader, vk_client, album)
        except ValueError:
            print("Вы указали неподходящий токен для ВКонтакте")
        except AttributeError:
            print("Вы указали неподходящий токен для Яндекс.Диска")
        except ImportError:
            print("На Диске закончилось место на диске")
        except FileExistsError:
            print('Этот вариант не сработал. Давайте попробуем еще раз')
        except FileNotFoundError:
            print('Доступ к альбому запрещён')