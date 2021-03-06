from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
# Create your views here.
from .models import Post, Comment, subComment
from .forms import EmailPostForm, CommentForm, subCommentForm,SearchForm
from taggit.models import Tag

class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    object_list = Post.published.all() #get all published articles
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in = [tag])
    
    paginator = Paginator(object_list, 3) # 每页显示3篇文章
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
    # 如果page参数不是一个整数就返回第一页
        posts = paginator.page(1)
    except EmptyPage:
    # 如果页数超出总页数就返回最后一页
        posts = paginator.page(paginator.num_pages)
        posts = Post.published.all()
    return render(request, 'blog/post/list.html', {'page':page, 'posts':posts, 'tag': tag})

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post,
                                   status='published',
                                   publish__year=year,
                                   publish__month=month,
                                   publish__day=day)
    # 列出文章对应的所有活动的评论
    print(post.id)
    comments = post.comments.filter(active=True) #comments is the foreign key to post data
    subComments = None
    for comment in comments:
        subComments = comment.subcomments.filter(active=True)
        print(subComments)
    new_comment = None
    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # 通过表单直接创建新数据对象，但是不要保存到数据库中
            new_comment = comment_form.save(commit=False)
            # 设置外键为当前文章
            new_comment.post = post
            # 将评论数据对象写入数据库
            new_comment.save()
    else:
        comment_form = CommentForm()
    post_tags_ids = post.tags.values_list('id',flat=True)
    similar_tags = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_tags.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    return render(request,
                  'blog/post/detail.html',
                  {'post': post, 'comments':comments, 'new_comment':new_comment, 'comment_form':comment_form, 'sub_comments':subComments,
                   'similar_posts':similar_posts})

def make_subcomment(request, comment_id, post_id):
    #comments = get_object_or_404(Comment, id=comment_id)
    post = get_object_or_404(Post, id=post_id, status='published')
    comments = get_object_or_404(post.comments, id=comment_id)
    print('*'*8, post_id, comment_id)
    print('#'*10,post.comments)
    print(comments)
    #print(comments)
    
    sent = False
    if request.method == 'POST':
        form = subCommentForm(data=request.POST)
        if form.is_valid():
                        # 通过表单直接创建新数据对象，但是不要保存到数据库中
            new_comment = form.save(commit=False)
            # 设置外键为当前文章
            new_comment.target = comments
            # 将评论数据对象写入数据库
            new_comment.save()
            sent =True
    else:
        form = subCommentForm()

    return render(request, 'blog/post/subcomment.html', {'comment':comments, 'form':form, 'sent':sent, 'post':post})


def post_share(request, post_id):
# 通过id 获取 post 对象

    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == "POST":
# 表单被提交
        form = EmailPostForm(request.POST)
        if form.is_valid():
    # 验证表单数据
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments:{}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, '', [cd['to']])
            sent = True
    # 发送邮件......
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent':sent})
    
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
            search_query = SearchQuery(query)
            results = Post.objects.annotate(search=search_vector,
                rank=SearchRank(search_vector, search_query)
                ).filter(rank__gte=0.3).order_by('-rank')
    return render(request, 'blog/post/search.html', {'query': query, "form": form, 'results': results})