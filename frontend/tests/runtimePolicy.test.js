import assert from 'node:assert/strict'
import test from 'node:test'

import { demoRowsForChannel, isUnauthorizedError } from '../src/services/runtimePolicy.js'

test('service channel never receives demo seed rows', () => {
  const demoRows = [{ id: 'demo-1', amount: 12000 }]

  assert.deepEqual(demoRowsForChannel(false, demoRows), [])
  assert.deepEqual(demoRowsForChannel(true, demoRows), demoRows)
  assert.notEqual(demoRowsForChannel(true, demoRows)[0], demoRows[0])
})

test('only an HTTP 401 response expires the stored session', () => {
  assert.equal(isUnauthorizedError({ response: { status: 401 } }), true)
  assert.equal(isUnauthorizedError({ response: { status: 403 } }), false)
  assert.equal(isUnauthorizedError(new Error('network unavailable')), false)
})
