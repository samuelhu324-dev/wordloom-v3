我想重新澄清一些概念：
1. Library：持有多个Bookshelfs的引用（见图2）比如我常用的QuickLog和一些日常事项的EverydayLog，他们都是书架；
2. Bookshelfs：从Library界面（图2）点击一个Bookshelf（比如我点击QuickLog）里面会有大量与此相关的Books（见图3），这就是Boolshelf QuickLog界面；
3. Books：Books即是Bookshelf里面的大量藏书，比如图3里面有各种各样的开发日志，实际上就是一本本的书；
4. Blocks：点开一本书（比如图4，你知道这本书叫D27-29WordloomDev）而你看到了一个个文本框，没错，比如”1. feat/Orbit-Note“就是一个Block；而一本书有多个Block类型和语块构成；
-- Block类型：即图4中比如CheckPoint（检查点）、文本框以及未来的Interpretation，都是Block类型
-- Block语块：即一个个由各种类型的Blocks构成的框，以此形成了一本本的Book；
5. 工具栏：比如你在图1提到的Tag、未来我要把CheckPoint的分段计时功能抽出成应用到所有Block类型，而非单一CheckPoint（这也意味着CheckPoint在以后可能不再是一个独立的Block，会被取下）Search功能（全Library搜索，全Bookshelf搜索以及全Book内搜索等复杂的筛选搜索机制）
以上是基本功能；
6. 主题/自定义界面美化：你可以从我给你的树状图看到有很多乱七八糟的styles, themes, tokens相关的文件；这些全部和界面主题相关；我的设想目前来说是：可以将自己的Library、Bookshelf、Book，除开固定的Block类型、工具内容外，用户可以随心所欲做拼贴（类似于现实的手账）和古早年代大家在用的QQ空间，但是也有很多默认和已经制作好的主题，可以直接套上去不费脑；所以我很好奇这应该是一个和Library平行的内容，一起放在左边菜单上（看图5）还是说这个功能内嵌在”工具栏“内，或者其实两者兼而有之，既是一个单独的子模块又是工具栏内嵌功能；
7. 以后整个系统要统计各项数据，Library、Theme以外还有单独的Stats模块要分出来构成在菜单栏左边（图5）；
8. Library (Loom和Orbit只是实验名现在功能即将合并，因为Loom其实就是一种Block类型，比如InterpretationBlock，而Orbit实际上就是目前的Library功能的雏形，只是还没清晰的架构)Theme、Stats、Chronicle和Preferences等；
![alt text](Domain5.png) ![alt text](Domain1.png) ![alt text](Domain2.png) ![alt text](Domain3.png) ![alt text](Domain4.png)