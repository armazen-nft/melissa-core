cmake_minimum_required(VERSION 3.16)
project(melissa_core C)

set(CMAKE_C_STANDARD 11)

find_package(PkgConfig REQUIRED)
set(LUA_PKG_CANDIDATES lua5.4 lua-5.4 lua54)
set(LUA_FOUND FALSE)
foreach(pkg IN LISTS LUA_PKG_CANDIDATES)
  pkg_check_modules(LUA54 QUIET ${pkg})
  if(LUA54_FOUND)
    set(LUA_FOUND TRUE)
    message(STATUS "Using Lua package: ${pkg}")
    break()
  endif()
endforeach()
if(NOT LUA_FOUND)
  message(FATAL_ERROR "Lua 5.4 not found via pkg-config (tried: ${LUA_PKG_CANDIDATES})")
endif()

add_library(melissa_lua_bridge STATIC
    src/lua_bridge.c
    src/lua_state_pool.c
    src/bindings/memory.c
    src/bindings/model.c
    src/bindings/bifurcation.c
)

target_include_directories(melissa_lua_bridge
    PUBLIC include
    PRIVATE src src/bindings ${LUA54_INCLUDE_DIRS}
)

target_compile_options(melissa_lua_bridge PRIVATE ${LUA54_CFLAGS_OTHER})
target_link_libraries(melissa_lua_bridge PRIVATE ${LUA54_LIBRARIES} pthread m)

add_executable(test_lua_bridge tests/test_lua_bridge.c)
target_include_directories(test_lua_bridge PRIVATE include ${LUA54_INCLUDE_DIRS})
target_link_libraries(test_lua_bridge PRIVATE melissa_lua_bridge ${LUA54_LIBRARIES} pthread m)
