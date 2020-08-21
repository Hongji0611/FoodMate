from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.base import View

from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.core import serializers

from .models import Photo, InsertedImage, Comment
from .forms import PhotoForm, ImageFormSet, CommentForm
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin

from django.db.models import Count
from django.http import HttpResponseForbidden
from urllib.parse import urlparse
from django.core.exceptions import ObjectDoesNotExist

import json


@login_required
def create(request):
    # ImageFormSet = modelformset_factory(Image, form=ImageForm, extra=4)
    if request.method == 'POST':
        photo_form = PhotoForm(request.POST, request.FILES)
        image_formset = ImageFormSet(request.POST, request.FILES)
        if photo_form.is_valid() and image_formset.is_valid():
            photo = photo_form.save(commit=False)
            photo.author_id = request.user.id

            with transaction.atomic():
                photo.save()
                image_formset.instance = photo
                image_formset.save()
                return redirect('/')
    else:
        photo_form = PhotoForm()
        image_formset = ImageFormSet()
    return render(request, 'photo/photo_create.html', {
        'photo_form': photo_form,
        'image_formset': image_formset,
    })


class PhotoDelete(DeleteView):
    model = Photo
    template_name_suffix = '_delete'
    success_url = '/'

    def dispatch(self, request, *args, **kwargs):
        object = self.get_object()
        if object.author != request.user:
            messages.warning(request, '삭제할 권한이 없습니다.')
            return HttpResponseRedirect('/')
        else:
            return super(PhotoDelete, self).dispatch(request, *args, **kwargs)


class PhotoDetail(LoginRequiredMixin, FormMixin, DetailView):
    model = Photo
    template_name_suffix = '_detail'
    context_object_name = "product"
    form_class = CommentForm

    # ~~시간 전
    # time = datetime.now()
    # model.time_now = str(time.month - model.updated.month)
    # if model.created.day == time.day:
    #     time_now = str(time.hour - model.created.hour) + "시간 전"
    # else:
    #     if model.updated.month == time.month:
    #         time_now = str(time.day - model.created.day) + "일 전"
    #     else:
    #         if model.updated.year == time.year:
    #             time_now = str(time.month - model.updated.month) + "개월 전"

    def get_success_url(self):  # post처리가 성공한뒤 행할 행동
        return reverse('photo:detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        # 기본 구현을 호출해 context를 가져온다.
        context = super().get_context_data(**kwargs)
        # 모든 책을 쿼리한 집합을 context 객체에 추가한다
        # comment_count = Photo.objects.values('category').annotate(Count('category'))

        temp = Comment.objects.all()
        count = 0
        for i in temp.all():
            if i.photo == self:
                count = count + 1

        context['image'] = InsertedImage.objects.all()
        context['form'] = CommentForm()
        context['comment'] = Comment.objects.all()
        context['comment_count'] = count

        return context

    def post(self, request, *args, **kwargs):  # post요청이 들어왔을때.
        self.object = self.get_object()  # 현재페이지 object get.
        form = self.get_form()  # form데이터 받아오기
        if form.is_valid():  # form의 내용이 정상적일 경우
            return self.form_valid(form)  # form_valid함수 콜
        else:
            return self.form_invalid(form)

    def form_valid(self, form):  # form_valid함수
        comment = form.save(commit=False)  # form데이터를 저장. 그러나 쿼리실행은 x
        comment.photo = get_object_or_404(Photo,
                                          pk=self.object.pk)  # photo object를 call하여 photocomment의 photo로 설정(댓글이 속할 게시글 설정) pk로 pk설정 pk - photo id
        comment.username = self.request.user  # 댓글쓴 사람 설정.
        comment.save()  # 수정된 내용대로 저장. 쿼리실행
        return super(PhotoDetail, self).form_valid(form)


def photo_list(request):  # 카테고리, 지역에 따라 list가 다릅니다\
    articles = Photo.objects.all()
    article_dict = {}
    # photo model을 key로 하고, image url을 value로 하는 맵 생성
    paginator = Paginator(articles, 10)  # 10개 제한
    page = request.GET.get('page')
    articles = paginator.get_page(page)

    for i in range(0, articles.__len__()):
        tmp = articles[i]
        img_obj = (InsertedImage.objects.get(photo=tmp))
        article_dict[articles[i]] = img_obj.image.url
    return render(request, "photo/photo_list.html",
                  {"data": article_dict, "raw_posts": articles})  # 가공하지 않은 article을 그대로 넘김


@csrf_exempt
def call_ajax(request):
    if request.method == 'POST':
        response_json = request.POST
        response_json = json.dumps(response_json)
        data = json.loads(response_json)  # ajax에서 넘겨주는 값을 받아옴

        counter = int(data['counter'])
        start_index = counter - 10  # 몇개씩 가져올것인지 설정, 지금은 10개. photo_list.js와 동시에 수정해줘야함
        end_index = counter
        tmp = Photo.objects.all()[start_index:end_index - 1]
        if not tmp.exists():  # 쿼리한 결과 더 읽어올 글이 없다면
            return JsonResponse({'status': 'false', 'message': 'No more contents to show'}, status=404)
        img_urls = []
        for i in range(0, tmp.count()):
            img_urls.append(InsertedImage.objects.get(photo=tmp[i]).image.url)

        articles = serializers.serialize('json', tmp)  # tmp 객체를 json 화 시키기
        data = {'articles': articles, 'img_urls': img_urls}
        return JsonResponse(data, safe=False)
    return JsonResponse({'status': 'false', 'message': 'This call only support POST method'}, status=400)


def photo_search(request):
    articles = Photo.objects.all()
    article_dict = {}

    # input에서 query_str라는 이름으로 정의한 input 값을 받아옴
    q = request.POST.get('query_str', '')
    if q:
        # 필드명__icontains -> 대소문자 상관없이 포함하고 있다면 (제목과 본문 내용 비교)
        searched_articles = articles.filter(Q(title__icontains=q) | Q(text__icontains=q))
    else:
        return render(request, "photo/photo_list.html")

    # photo_list와 마찬가지로 딕셔너리 생성
    for i in range(0, searched_articles.count()):
        tmp = searched_articles[i]
        img_obj = (InsertedImage.objects.get(photo=tmp))
        article_dict[searched_articles[i]] = img_obj.image.url
    return render(request, "photo/photo_list.html", {"data": article_dict})


class PhotoLike(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:  # 로그인이 되어있지 않을 경우
            return HttpResponseForbidden()  # 아무일도 일어나지 않는다
        else:
            if 'photo_id' in kwargs:
                photo_id = kwargs['photo_id']
                photo = Photo.objects.get(pk=photo_id)
                user = request.user
                if user in photo.like.all():
                    photo.like.remove(user)
                else:
                    photo.like.add(user)

            referer_url = request.META.get('HTTP_REFERER')  # 성공했을 때 url을 옮기지 않고
            path = urlparse(referer_url).path
            return HttpResponseRedirect(path)


def my_activity(request):
    articles = Photo.objects.all()
    img = InsertedImage.objects.all()
    comment = Comment.objects.all()
    article_dict1 = {}
    article_dict2 = {}
    article_dict3 = {}

    count1 = 0
    count2 = 0
    count3 = 0

    flag1 = 1
    flag2 = 1
    flag3 = 1

    for i in range(1, comment.count() + 1):
        temp = comment.get(pk=i)
        if temp.username == request.user:
            photo_tmp = temp.photo
            count2 = count2 + 1
            if flag2 == 1:
                for j in range(1, articles.count() + 1):
                    if img.get(pk=j).photo == photo_tmp:
                        img_obj = img.get(pk=j)
                        flag2 = 0
                        break
                article_dict2[photo_tmp] = img_obj.image.url

    # photo model을 key로 하고, image url을 value로 하는 맵 생성
    for i in range(1, articles.count() + 1):
        tmp = articles.get(pk=i)
        if tmp.author == request.user:
            count1 = count1 + 1
            if flag1 == 1:
                for j in range(1, articles.count() + 1):
                    if img.get(pk=j).photo == tmp:
                        img_obj = img.get(pk=j)
                        flag1 = 0
                        break
                article_dict1[articles.get(pk=i)] = img_obj.image.url

        for like_temp in tmp.like.all():
            if like_temp == request.user:
                count3 = count3 + 1
                if flag3 == 1:
                    for j in range(1, articles.count() + 1):
                        if img.get(pk=j).photo == tmp:
                            img_obj = img.get(pk=j)
                            flag3 = 0
                            break
                    article_dict3[articles.get(pk=i)] = img_obj.image.url

    return render(request, "photo/my_activity.html",
                  {"data1": article_dict1, "data2": article_dict2, "data3": article_dict3, "count1": count1,
                   "count2": count2, "count3": count3})


def written_photo(request):
    articles = Photo.objects.all()
    img = InsertedImage.objects.all()
    article_dict = {}
    count = 0
    # photo model을 key로 하고, image url을 value로 하는 맵 생성
    for i in range(1, articles.count() + 1):
        tmp = articles.get(pk=i)
        for j in range(1, articles.count() + 1):
            if img.get(pk=j).photo == tmp:
                img_obj = img.get(pk=j)
                break
        if tmp.author == request.user:
            article_dict[articles.get(pk=i)] = img_obj.image.url
            count = count + 1

    return render(request, "photo/written_photo.html", {"data": article_dict, "count": count})


def comment_photo(request):
    articles = Photo.objects.all()
    img = InsertedImage.objects.all()
    comment = Comment.objects.all()
    article_dict = {}
    count = 0
    # photo model을 key로 하고, image url을 value로 하는 맵 생성
    for i in range(1, comment.count() + 1):
        temp = comment.get(pk=i)
        if temp.username == request.user:
            photo_tmp = temp.photo
            for j in range(1, articles.count() + 1):
                if img.get(pk=j).photo == photo_tmp:
                    img_obj = img.get(pk=j)
                    break
            article_dict[photo_tmp] = img_obj.image.url
            count = count + 1
    return render(request, "photo/comment_photo.html", {"data": article_dict, "count": count})


def like_photo(request):
    articles = Photo.objects.all()
    img = InsertedImage.objects.all()
    article_dict = {}
    count = 0
    # photo model을 key로 하고, image url을 value로 하는 맵 생성
    for i in range(1, articles.count() + 1):
        tmp = articles.get(pk=i)
        for like_temp in tmp.like.all():
            if like_temp == request.user:
                for j in range(1, articles.count() + 1):
                    if img.get(pk=j).photo == tmp:
                        img_obj = img.get(pk=j)
                        break
                article_dict[articles.get(pk=i)] = img_obj.image.url
                count = count + 1
    return render(request, "photo/like_photo.html", {"data": article_dict, "count": count})
