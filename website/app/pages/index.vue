<template>
  <div class="app-container">
    <AppNavbar />
    <div class="workspace">
      <Sidebar />
      <PreviewArea />
    </div>
    <SettingsDialog />

  </div>
</template>

<style>
/* Reset Body */
body { margin: 0; padding: 0; background: var(--el-bg-color-page); }
</style>

<style scoped>
.app-container {
  display: flex; flex-direction: column; height: 100vh;
}
.workspace {
  flex: 1; display: flex; overflow: hidden;
}
</style>