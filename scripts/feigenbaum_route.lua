_required_api_version = 1

function run(payload)
  local adapted = melissa.adapt({ delta = melissa.FEIGENBAUM_DELTA, memory_tier = melissa.MEM_LONG_TERM })
  local ok = melissa.bifurcation_hint(adapted.delta, payload)
  if not ok then
    return '{"status":"bifurcation-rejected"}'
  end

  local memory = melissa.memory_get_string('route_seed', adapted.memory_tier) or 'default-seed'
  local infer = melissa.model_infer('feigenbaumia-v1', payload .. ':' .. memory) or 'noop'
  melissa.memory_write('last_infer', infer, melissa.MEM_EPHEMERAL)

  return melissa.json_encode({
    status = 'ok',
    delta = adapted.delta,
    infer = infer,
    memory = memory
  })
end
