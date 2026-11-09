import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import test from 'node:test'

const frontend = new URL('../', import.meta.url)

test('brands the document, navigation and placeholder for IndustrialOps', async () => {
  const index = await readFile(new URL('index.html', frontend), 'utf8')
  const app = await readFile(new URL('src/App.vue', frontend), 'utf8')

  assert.match(index, /<title>IndustrialOps Copilot<\/title>/)
  assert.match(app, /<nav[\s\S]*IndustrialOps Copilot[\s\S]*<\/nav>/)
  assert.match(app, /<h1>IndustrialOps Copilot<\/h1>/)
})

test('excludes legacy branding and feature navigation from frontend source', async () => {
  const src = new URL('src/', frontend)
  const sources = await readdir(src, { recursive: true, withFileTypes: true })
  const forbidden = /heritage|craft|knowledge.?graph|\bgraph\b|非遗|图谱/i

  for (const source of sources.filter((entry) => entry.isFile())) {
    assert.doesNotMatch(await readFile(`${source.parentPath}/${source.name}`, 'utf8'), forbidden)
  }

  const manifest = await readFile(new URL('package.json', frontend), 'utf8')
  assert.doesNotMatch(manifest, forbidden)
})
