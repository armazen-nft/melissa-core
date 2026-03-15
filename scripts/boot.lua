local function json_escape(s)
  s = s:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n')
  return '"' .. s .. '"'
end

melissa.json_encode = function(tbl)
  local out = {}
  table.insert(out, '{')
  local first = true
  for k, v in pairs(tbl) do
    if not first then table.insert(out, ',') end
    first = false
    table.insert(out, json_escape(tostring(k)))
    table.insert(out, ':')
    if type(v) == 'string' then
      table.insert(out, json_escape(v))
    else
      table.insert(out, tostring(v))
    end
  end
  table.insert(out, '}')
  return table.concat(out)
end

melissa.memory_get_string = function(key, tier)
  return melissa.memory_read(key, tier)
end

melissa.memory_get_number = function(key, tier)
  local v = melissa.memory_read(key, tier)
  if v == nil then return nil end
  return tonumber(v)
end

melissa.adapt = function(route)
  route = route or {}
  route.delta = route.delta or melissa.FEIGENBAUM_DELTA
  route.memory_tier = route.memory_tier or melissa.MEM_SHORT_TERM
  return route
end
