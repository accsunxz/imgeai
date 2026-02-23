<template>
  <div class="app-container">
    <AppNavbar />

    <div class="workspace">
      <Sidebar />
      <PreviewArea />
    </div>

    <SettingsDialog/>
    <ConfigViewerDialog />
  </div>
</template>

<style>
body { margin: 0; padding: 0; background: #f8fafc; font-family: system-ui, sans-serif; }
</style>

<style scoped>
.app-container { display: flex; flex-direction: column; height: 100vh; }
.workspace { flex: 1; display: flex; overflow: hidden; }
</style>