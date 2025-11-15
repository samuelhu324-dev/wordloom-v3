frontend/
  app/
    library/
      [libraryId]/
        book/
          [bookId]/
            page.tsx          ← 页面入口（很薄）
  modules/
    book/
      ui/
        BookEditorPage.tsx
      hooks/
        useBookEditor.ts
      api/
        bookApi.ts
      model/
        bookTypes.ts
    block/
      ui/
        BlockList.tsx
        BlockItem.tsx
      hooks/
        useBlockCommands.ts
      api/
        blockApi.ts
      model/
        blockTypes.ts


先有“壳 +骨架”，再慢慢填肉，是非常行业化的做法

很多团队上新项目的顺序其实就是：

定 layout & design tokens（你现在就可以做）；

做 AppShell + Sidebar + Topbar 这些基础壳；

选一个最核心的 user flow 做 vertical slice；

其余模块暂时只做“空页面 + 占位文案”，
但都挂在统一 layout 下，这样架子不会乱。

你现在完全可以照这个模式来：

今天 / 明天：

建好 tokens.css；

搞定 AppShell / Sidebar / Topbar 的最小版本；

把 Book 编辑页那条路打通；

再往后几天：

把 Library/Bookshelf 页面接上；

接 Search；

给 Tag/Media 放几个简单占位页面（哪怕只是“Coming soon，但 API 结构已经订好”）。

这样一来，你前端也会像现在的后端一样：
有清晰的壳，有稳住的 core，有一条能 demo 的完整路径，其余模块随时能长肉。